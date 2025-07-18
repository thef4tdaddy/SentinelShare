

// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverComponentsExternalPackages: ['imap', 'nodemailer']
  }
}

module.exports = nextConfig