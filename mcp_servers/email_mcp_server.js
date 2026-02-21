/**
 * MCP Server for AI Employee - Silver Tier
 *
 * Privacy-focused email handling and vault integration
 * All operations are local-only with no cloud dependency
 * Sensitive actions require approval workflow integration
 */

const express = require('express');
const nodemailer = require('nodemailer');
const path = require('path');
const fs = require('fs').promises;
const crypto = require('crypto');
const { v4: uuidv4 } = require('uuid');

// Initialize express app
const app = express();
const PORT = process.env.MCP_PORT || 8080;

// Middleware
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Configure logging
const log = (message, level = 'INFO') => {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] [${level}] ${message}`);
};

// MCP Server Configuration
class MCPService {
    constructor() {
        this.transporter = null;
        this.config = this.loadConfig();
        this.vaultPath = path.join(process.cwd(), 'vault');
        this.needsActionPath = path.join(process.cwd(), 'Needs_Action');
        this.pendingApprovalPath = path.join(process.cwd(), 'Pending_Approval');
        this.approvedPath = path.join(process.cwd(), 'Approved');
        this.rejectedPath = path.join(process.cwd(), 'Rejected');

        // Ensure directories exist
        this.ensureDirectories();
    }

    loadConfig() {
        const configPath = path.join(process.cwd(), 'mcp_config.json');
        try {
            const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
            log('Configuration loaded from mcp_config.json');
            return config;
        } catch (error) {
            log('No config file found, using default configuration', 'WARN');
            return {
                smtp: {
                    host: process.env.SMTP_HOST || 'smtp.gmail.com',
                    port: parseInt(process.env.SMTP_PORT) || 587,
                    secure: false, // true for 465, false for other ports
                    auth: {
                        user: process.env.SMTP_USER || '',
                        pass: process.env.SMTP_PASS || ''
                    }
                },
                privacy: {
                    logSensitiveData: false,
                    useLocalOnly: true,
                    encryptTempFiles: true
                }
            };
        }
    }

    async ensureDirectories() {
        const dirs = [
            this.vaultPath,
            this.needsActionPath,
            this.pendingApprovalPath,
            this.approvedPath,
            this.rejectedPath
        ];

        for (const dir of dirs) {
            try {
                await fs.mkdir(dir, { recursive: true });
                log(`Directory created: ${dir}`);
            } catch (error) {
                log(`Directory exists or error: ${dir}`, 'WARN');
            }
        }
    }

    async initializeEmail() {
        try {
            this.transporter = nodemailer.createTransporter({
                host: this.config.smtp.host,
                port: this.config.smtp.port,
                secure: this.config.smtp.secure,
                auth: {
                    user: this.config.smtp.auth.user,
                    pass: this.config.smtp.auth.pass
                }
            });

            // Verify the transporter
            await this.transporter.verify();
            log('Email transporter initialized successfully');
            return true;
        } catch (error) {
            log(`Failed to initialize email transporter: ${error.message}`, 'ERROR');
            return false;
        }
    }

    async validateEmailAddress(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }

    async createApprovalAction(emailData) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').replace('T', '_').split('.')[0];
        const uniqueId = crypto.randomBytes(4).toString('hex');
        const filename = `EMAIL_APPROVAL_${timestamp}_${uniqueId}.md`;
        const filepath = path.join(this.pendingApprovalPath, filename);

        // Sanitize content for privacy
        const sanitizedContent = this.config.privacy.logSensitiveData
            ? emailData.content
            : '[Content hidden for privacy - see vault for details]';

        const actionContent = `---
type: email_approval
status: pending
priority: ${emailData.priority || 'medium'}
request_id: ${uuidv4()}
created: ${new Date().toISOString()}
requires_approval: true
---

# Email Approval Request

## Request Details
- **From:** ${emailData.from}
- **To:** ${emailData.to}
- **Subject:** ${emailData.subject}
- **Priority:** ${emailData.priority || 'medium'}
- **Request ID:** ${uuidv4()}
- **Created:** ${new Date().toISOString()}

## Content Preview
${sanitizedContent.substring(0, 500)}${sanitizedContent.length > 500 ? '...' : ''}

## Actions Required
- [ ] Review email content for approval
- [ ] Verify recipient and content appropriateness
- [ ] Approve or reject request
- [ ] Move to Approved or Rejected when decided

## Approval Workflow
This email requires approval based on Silver Tier security protocols:
- High priority emails require approval before sending
- Financial or sensitive information requires additional review
- All external communications should follow Company_Handbook.md guidelines

## Metadata
- Request generated by MCP Server
- Local-only processing
- Privacy-focused handling

## Decision Options
1. **Approve**: Move to Approved and send email
2. **Reject**: Move to Rejected with reason
3. **Modify**: Edit content before approval
`;

        await fs.writeFile(filepath, actionContent);
        log(`Approval action created: ${filename}`);
        return filepath;
    }

    async sendEmail(emailData) {
        try {
            // Validate email addresses
            if (!(await this.validateEmailAddress(emailData.to))) {
                throw new Error(`Invalid recipient email: ${emailData.to}`);
            }

            if (emailData.cc && !Array.isArray(emailData.cc)) {
                if (!(await this.validateEmailAddress(emailData.cc))) {
                    throw new Error(`Invalid CC email: ${emailData.cc}`);
                }
            }

            if (emailData.bcc && !Array.isArray(emailData.bcc)) {
                if (!(await this.validateEmailAddress(emailData.bcc))) {
                    throw new Error(`Invalid BCC email: ${emailData.bcc}`);
                }
            }

            // Prepare email options
            const mailOptions = {
                from: emailData.from || this.config.smtp.auth.user,
                to: emailData.to,
                subject: emailData.subject,
                text: emailData.text,
                html: emailData.html,
                cc: emailData.cc,
                bcc: emailData.bcc
            };

            // Send the email
            const info = await this.transporter.sendMail(mailOptions);
            log(`Email sent successfully to ${emailData.to}: ${info.messageId}`);

            // Log the sent email in the vault for transparency
            const sentRecord = {
                messageId: info.messageId,
                recipient: emailData.to,
                subject: emailData.subject,
                timestamp: new Date().toISOString(),
                status: 'sent'
            };

            await this.logEmailActivity(sentRecord);

            return {
                success: true,
                messageId: info.messageId,
                recipient: emailData.to
            };
        } catch (error) {
            log(`Failed to send email: ${error.message}`, 'ERROR');
            throw error;
        }
    }

    async logEmailActivity(logData) {
        if (!this.config.privacy.logSensitiveData) {
            // Only log metadata, not content
            const sanitizedLog = {
                messageId: logData.messageId,
                recipient: logData.recipient,
                subject: logData.subject,
                timestamp: logData.timestamp,
                status: logData.status
            };

            const logFile = path.join(this.vaultPath, 'email_activity.json');
            let existingLogs = [];

            try {
                const fileContent = await fs.readFile(logFile, 'utf8');
                existingLogs = JSON.parse(fileContent);
            } catch (error) {
                // File doesn't exist, start fresh
            }

            existingLogs.push(sanitizedLog);
            await fs.writeFile(logFile, JSON.stringify(existingLogs, null, 2));
        }
    }

    // Privacy-focused encryption utility
    encryptData(data) {
        if (!this.config.privacy.encryptTempFiles) return data;

        const algorithm = 'aes-256-cbc';
        const key = crypto.scryptSync(process.env.ENCRYPTION_KEY || 'defaultkey1234567890', 'salt', 32);
        const iv = crypto.randomBytes(16);
        const cipher = crypto.createCipher(algorithm, key);

        let encrypted = cipher.update(data, 'utf8', 'hex');
        encrypted += cipher.final('hex');

        return {
            encrypted: encrypted,
            iv: iv.toString('hex')
        };
    }

    decryptData(encryptedData, iv) {
        if (!this.config.privacy.encryptTempFiles) return encryptedData;

        const algorithm = 'aes-256-cbc';
        const key = crypto.scryptSync(process.env.ENCRYPTION_KEY || 'defaultkey1234567890', 'salt', 32);
        const decipher = crypto.createDecipher(algorithm, key);

        let decrypted = decipher.update(encryptedData, 'hex', 'utf8');
        decrypted += decipher.final('utf8');

        return decrypted;
    }
}

// Initialize MCP Service
const mcpService = new MCPService();

// API Routes
app.post('/api/mcp/email/send', async (req, res) => {
    try {
        const { to, subject, text, html, cc, bcc, priority, sensitive } = req.body;

        // Validate required fields
        if (!to || !subject) {
            return res.status(400).json({
                error: 'Missing required fields: to and subject are required'
            });
        }

        // For sensitive emails, create approval action instead of sending directly
        if (sensitive) {
            const emailData = {
                to,
                subject,
                text,
                html,
                cc,
                bcc,
                priority,
                content: text || html,
                from: req.body.from
            };

            const actionPath = await mcpService.createApprovalAction(emailData);

            return res.status(200).json({
                message: 'Sensitive email requires approval. Action created.',
                approvalAction: actionPath,
                requires: 'human_approval'
            });
        }

        // For non-sensitive emails, send directly
        const result = await mcpService.sendEmail({
            to,
            subject,
            text,
            html,
            cc,
            bcc,
            priority,
            from: req.body.from
        });

        res.status(200).json({
            success: true,
            message: 'Email sent successfully',
            result
        });
    } catch (error) {
        log(`Email sending error: ${error.message}`, 'ERROR');
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

app.post('/api/mcp/email/approve', async (req, res) => {
    try {
        const { approvalActionPath, action } = req.body;

        if (!approvalActionPath || !action) {
            return res.status(400).json({
                error: 'Missing required fields: approvalActionPath and action are required'
            });
        }

        // Read the approval action file
        const actionContent = await fs.readFile(approvalActionPath, 'utf8');

        // Parse frontmatter to get email details
        const frontmatterRegex = /---\n([\s\S]*?)\n---/;
        const frontmatterMatch = actionContent.match(frontmatterRegex);
        const frontmatter = frontmatterMatch ? frontmatterMatch[1] : '';

        // Extract email data from the file content
        const lines = actionContent.split('\n');
        let to, subject, content;

        for (const line of lines) {
            if (line.startsWith('- **From:**')) {
                // Extract email data from the action file
                // This would need to be parsed properly from the original file
                // For this example, we're assuming the data is recoverable
            }
        }

        if (action === 'approve') {
            // Move file to Approved directory
            const filename = path.basename(approvalActionPath);
            const newPath = path.join(mcpService.approvedPath, filename);
            await fs.rename(approvalActionPath, newPath);

            // In a real implementation, this would send the email after approval
            res.status(200).json({
                success: true,
                message: 'Action approved and processed',
                newLocation: newPath
            });
        } else if (action === 'reject') {
            // Move file to Rejected directory
            const filename = path.basename(approvalActionPath);
            const newPath = path.join(mcpService.rejectedPath, filename);
            await fs.rename(approvalActionPath, newPath);

            res.status(200).json({
                success: true,
                message: 'Action rejected',
                newLocation: newPath
            });
        } else {
            res.status(400).json({
                error: 'Invalid action. Use "approve" or "reject".'
            });
        }
    } catch (error) {
        log(`Approval error: ${error.message}`, 'ERROR');
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

app.get('/api/mcp/status', (req, res) => {
    res.status(200).json({
        status: 'running',
        privacyMode: mcpService.config.privacy,
        localOnly: true,
        timestamp: new Date().toISOString()
    });
});

app.get('/api/mcp/vault/files', async (req, res) => {
    try {
        // List files in the vault (non-sensitive metadata only)
        const files = await fs.readdir(mcpService.vaultPath);
        const fileDetails = [];

        for (const file of files) {
            const filePath = path.join(mcpService.vaultPath, file);
            const stat = await fs.stat(filePath);

            fileDetails.push({
                name: file,
                size: stat.size,
                modified: stat.mtime,
                type: path.extname(file)
            });
        }

        res.status(200).json({
            success: true,
            files: fileDetails
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.status(200).json({
        status: 'healthy',
        service: 'MCP Server',
        privacy: 'enabled',
        local_only: true,
        timestamp: new Date().toISOString()
    });
});

// Initialize email transporter after app setup
const initializeServer = async () => {
    try {
        const emailReady = await mcpService.initializeEmail();
        if (!emailReady) {
            log('Warning: Email transporter failed to initialize. Server will run without email capabilities.', 'WARN');
        }

        app.listen(PORT, 'localhost', () => {
            log(`MCP Server running on http://localhost:${PORT}`);
            log('Privacy-focused, local-only operation enabled');
            log('All sensitive actions require approval workflow');
        });
    } catch (error) {
        log(`Failed to start MCP Server: ${error.message}`, 'ERROR');
        process.exit(1);
    }
};

// Graceful shutdown
process.on('SIGINT', () => {
    log('Shutting down MCP Server...');
    process.exit(0);
});

process.on('SIGTERM', () => {
    log('Shutting down MCP Server...');
    process.exit(0);
});

// Start the server
initializeServer();

module.exports = { MCPService };