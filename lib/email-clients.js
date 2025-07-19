// lib/email-clients.js
import Imap from "imap";
import { simpleParser } from "mailparser";
import nodemailer from "nodemailer";

export class GmailClient {
  constructor() {
    this.config = {
      user: process.env.GMAIL_EMAIL,
      password: process.env.GMAIL_APP_PASSWORD,
      host: "imap.gmail.com",
      port: 993,
      tls: true,
      tlsOptions: { rejectUnauthorized: false },
    };
  }

  async getRecentEmails(since = new Date(Date.now() - 24 * 60 * 60 * 1000)) {
    return new Promise((resolve, reject) => {
      const imap = new Imap(this.config);
      const emails = [];

      imap.once("ready", () => {
        imap.openBox("INBOX", true, (err) => {
          if (err) return reject(err);

          const searchCriteria = ["UNSEEN", ["SINCE", since]];
          imap.search(searchCriteria, (err, results) => {
            if (err) return reject(err);
            if (!results.length) return resolve([]);

            const fetch = imap.fetch(results, { bodies: "" });

            fetch.on("message", (msg) => {
              let buffer = "";
              msg.on("body", (stream) => {
                stream.on(
                  "data",
                  (chunk) => (buffer += chunk.toString("utf8"))
                );
                stream.once("end", async () => {
                  try {
                    const parsed = await simpleParser(buffer);
                    emails.push({
                      id:
                        parsed.messageId ||
                        `gmail-${Date.now()}-${Math.random()}`,
                      subject: parsed.subject || "No Subject",
                      from: parsed.from?.text || "Unknown Sender",
                      to: parsed.to?.text || "",
                      date: parsed.date || new Date(),
                      body: parsed.text || parsed.html || "",
                      source: "gmail",
                    });
                  } catch (e) {
                    console.error("Parse error:", e);
                  }
                });
              });
            });

            fetch.once("end", () => {
              imap.end();
              resolve(emails);
            });
          });
        });
      });

      imap.once("error", reject);
      imap.connect();
    });
  }
}

export class ICloudClient {
  constructor() {
    this.config = {
      user: process.env.ICLOUD_EMAIL,
      password: process.env.ICLOUD_PASSWORD,
      host: "imap.mail.me.com",
      port: 993,
      tls: true,
      tlsOptions: { rejectUnauthorized: false },
    };
  }

  async getRecentEmails(since = new Date(Date.now() - 24 * 60 * 60 * 1000)) {
    return new Promise((resolve, reject) => {
      const imap = new Imap(this.config);
      const emails = [];

      imap.once("ready", () => {
        imap.openBox("INBOX", true, (err) => {
          if (err) return reject(err);

          const searchCriteria = ["UNSEEN", ["SINCE", since]];
          imap.search(searchCriteria, (err, results) => {
            if (err) return reject(err);
            if (!results.length) return resolve([]);

            const fetch = imap.fetch(results, { bodies: "" });

            fetch.on("message", (msg) => {
              let buffer = "";
              msg.on("body", (stream) => {
                stream.on(
                  "data",
                  (chunk) => (buffer += chunk.toString("utf8"))
                );
                stream.once("end", async () => {
                  try {
                    const parsed = await simpleParser(buffer);
                    emails.push({
                      id:
                        parsed.messageId ||
                        `icloud-${Date.now()}-${Math.random()}`,
                      subject: parsed.subject || "No Subject",
                      from: parsed.from?.text || "Unknown Sender",
                      to: parsed.to?.text || "",
                      date: parsed.date || new Date(),
                      body: parsed.text || parsed.html || "",
                      source: "icloud",
                    });
                  } catch (e) {
                    console.error("Parse error:", e);
                  }
                });
              });
            });

            fetch.once("end", () => {
              imap.end();
              resolve(emails);
            });
          });
        });
      });

      imap.once("error", reject);
      imap.connect();
    });
  }
}

export class EmailSender {
  constructor() {
    this.transporter = nodemailer.createTransport({
      service: "gmail",
      auth: {
        user: process.env.SENDER_EMAIL,
        pass: process.env.SENDER_PASSWORD,
      },
    });
  }

  async sendEmail(to, subject, body) {
    try {
      await this.transporter.sendMail({
        from: process.env.SENDER_EMAIL,
        to,
        subject,
        html: body,
      });
      return true;
    } catch (error) {
      console.error("Send error:", error);
      return false;
    }
  }
}
