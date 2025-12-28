import fnmatch
import os
import re
from typing import Any, Dict, Optional

from sqlmodel import Session, select

from backend.models import ManualRule, ProcessedEmail


class LearningService:
    """
    Analyzes historical 'blocked' or 'ignored' emails that the user marked as 'should have been a receipt'.
    Generates new ManualRule suggestions based on common patterns.
    """

    @staticmethod
    def generate_rule_from_email(email: ProcessedEmail) -> Optional[Dict[str, Any]]:
        """
        Creates a suggested ManualRule based on a single email's properties.
        Focuses on domain-level and subject keyword patterns.
        """
        s_text = (email.sender or "").lower()
        b_text = (email.subject or "").lower()

        # 1. Extract domain
        domain_match = re.search(r"@([\w.-]+)", s_text)
        domain = domain_match.group(1) if domain_match else s_text

        # 2. Extract common keywords from subject (excluding common noise)
        noise = {
            "re:",
            "fwd:",
            "the",
            "and",
            "your",
            "order",
            "confirmation",
            "receipt",
        }
        keywords = [
            word
            for word in re.findall(r"\w+", b_text)
            if word not in noise and len(word) > 3
        ]

        # 3. Suggest a rule
        # If it's a clear store domain, suggest an email pattern
        suggested_rule = {
            "email_pattern": f"*@{domain}",
            "subject_pattern": None,
            "purpose": f"Learned from {email.sender}",
            "confidence": 0.7,  # Initial confidence
        }

        # If the subject has very specific keywords, suggest a subject pattern too
        if keywords:
            # Take the most unique keyword or first two
            suggested_rule["subject_pattern"] = f"*{keywords[0]}*"
            suggested_rule["confidence"] = (
                float(suggested_rule["confidence"] or 0.0) + 0.1
            )

        return suggested_rule

    @staticmethod
    def run_shadow_mode(session: Session, email_data: Dict[str, Any]):
        """
        Tests 'shadow mode' rules against an email.
        If a rule matches, increment its match_count and confidence.
        """
        subject = email_data.get("subject", "").lower()
        sender = email_data.get("from", "").lower()

        shadow_rules = session.exec(
            select(ManualRule).where(ManualRule.is_shadow_mode)
        ).all()

        for rule in shadow_rules:
            matches = True
            if rule.email_pattern and not fnmatch.fnmatch(
                sender, rule.email_pattern.lower()
            ):
                matches = False
            if (
                matches
                and rule.subject_pattern
                and not fnmatch.fnmatch(subject, rule.subject_pattern.lower())
            ):
                matches = False

            if matches:
                rule.match_count += 1
                # Slowly increase confidence with each successful match
                rule.confidence = min(1.0, rule.confidence + 0.05)
                session.add(rule)

        session.commit()

    @staticmethod
    def auto_promote_rules(session: Session):
        """
        Promote shadow rules to active ManualRule status if they hit 0.9 confidence and 3 matches.
        """
        auto_promote_confidence = float(
            os.getenv("AUTO_PROMOTE_CONFIDENCE_THRESHOLD", "0.9")
        )
        auto_promote_matches = int(os.getenv("AUTO_PROMOTE_MATCH_COUNT_THRESHOLD", "3"))

        candidates = session.exec(
            select(ManualRule)
            .where(ManualRule.is_shadow_mode)
            .where(ManualRule.confidence >= auto_promote_confidence)
            .where(ManualRule.match_count >= auto_promote_matches)
        ).all()

        for rule in candidates:
            rule.is_shadow_mode = False
            rule.purpose = f"(AUTO) {rule.purpose}"
            session.add(rule)
            print(
                f"🚀 Auto-promoted rule: {rule.email_pattern} | {rule.subject_pattern}"
            )

        session.commit()

    @staticmethod
    def scan_history(session: Session, days: int = 30) -> int:
        """
        Scans email history for the last N days to find missed receipts.
        Creates LearningCandidate entries for findings.
        Returns the number of new candidates found.
        """
        from backend.models import LearningCandidate, ProcessedEmail
        from backend.services.detector import ReceiptDetector
        from backend.services.email_service import EmailService

        print(f"🕵️‍♂️ Starting Retroactive Scan (Last {days} days)...")
        # settings = EmailService.load_settings()
        # email_accounts = settings.get("email_accounts", [])

        # Use existing method
        email_accounts = EmailService.get_all_accounts()

        if not email_accounts:
            print("⚠️ No email accounts configured.")
            return 0

        total_new_candidates = 0

        # Calculate cutoff date
        # cutoff_date = utc_now() - timedelta(days=days)

        for idx, acct in enumerate(email_accounts):
            user = acct["email"]
            pwd = acct["password"]

            # Create a non-sensitive label for logging that is not derived from credentials
            account_label = f"account-{idx+1}"

            # Use EmailService logic but force the lookback
            # We need to act like fetch_recent_emails but strictly for this window
            # Implementation re-use: we can instantiate EmailService or use a specialized fetch
            # For simplicity & privacy, we fetch headers + body here using the same robust logic

            try:
                # Re-use EmailService's fetching logic logic via a temporary instance or direct call
                # Ideally, EmailService should expose a 'fetch_emails(since_date)' method
                # Since it relies on env var, we might need a small refactor or just direct usage
                # For now, let's assume we can use the existing fetch_recent_emails but we might need
                # to temporarily override the lookback or add a param to it.
                # Let's add a `custom_lookback_days` param to fetch_recent_emails in a separate step if needed.
                # Or better, we just reproduce the fetch logic here to ensure it's isolated.

                # ... actually, better to reuse code.
                # Let's call EmailService.fetch_recent_emails but we need to ensure it returns EVERYTHING
                # not just "unseen" if that was a restriction.
                # Current fetch_recent_emails uses SINCE date, which is perfect.
                # We just need to make sure we don't filter out things we already have...
                # Actually fetch_recent_emails DOESN'T filter by DB presence, it just returns list of dicts.

                # So:
                # 1. Fetch all emails from last N days
                # simplistic provider mapping
                imap_server = acct.get("imap_server", "imap.gmail.com")

                fetched = EmailService.fetch_recent_emails(
                    username=user,
                    password=pwd,
                    imap_server=imap_server,
                    lookback_days=days,
                )

                print(f"   > Account {account_label}: Fetched {len(fetched)} emails.")

                for email_data in fetched:
                    msg_id = email_data.get("message_id")
                    subject = email_data.get("subject", "")
                    body = email_data.get("body", "")
                    sender = email_data.get("from", "")

                    # Check if already processed
                    existing = session.exec(
                        select(ProcessedEmail).where(ProcessedEmail.email_id == msg_id)
                    ).first()

                    if existing:
                        continue  # Already handled

                    # Not in DB? Check if it looks like a receipt
                    # Construct minimal email dict for detector
                    email_obj = {
                        "subject": subject,
                        "body": body,
                        "sender": sender,
                        "from": sender,
                    }
                    is_receipt = ReceiptDetector.is_receipt(email_obj)

                    if is_receipt:
                        # FOUND ONE!
                        # Check if we already have a candidate for this pattern
                        # Deduplication strategy: Group by Sender + Subject (simplified)

                        # Generate a "suggested rule" to extract patterns
                        # We can reuse generate_rule_from_email if we mock a ProcessedEmail

                        dummy_email = ProcessedEmail(
                            sender=sender, subject=subject, body=body
                        )
                        rule_suggestion = LearningService.generate_rule_from_email(
                            dummy_email
                        )

                        if rule_suggestion:
                            # Check for existing candidate
                            existing_cand = session.exec(
                                select(LearningCandidate)
                                .where(LearningCandidate.sender == sender)
                                .where(
                                    LearningCandidate.subject_pattern
                                    == rule_suggestion["subject_pattern"]
                                )
                            ).first()

                            if existing_cand:
                                existing_cand.matches += 1
                                session.add(existing_cand)
                            else:
                                new_cand = LearningCandidate(
                                    sender=sender,
                                    subject_pattern=rule_suggestion["subject_pattern"],
                                    confidence=rule_suggestion["confidence"],
                                    example_subject=subject,
                                    type="Receipt",
                                )
                                session.add(new_cand)
                                total_new_candidates += 1

            except Exception as e:
                # Avoid logging potentially sensitive account identifiers; log only generic error info
                print(f"❌ Error during retroactive scan: {type(e).__name__}: {e}")

        session.commit()
        return total_new_candidates
