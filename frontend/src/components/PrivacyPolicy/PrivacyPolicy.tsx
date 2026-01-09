import Card, { CardContent, CardHeader, CardTitle } from '../ui/Card';

export default function PrivacyPolicy() {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Privacy Policy</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Last updated: January 2025
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>1. Information We Collect</CardTitle>
        </CardHeader>
        <CardContent className="prose dark:prose-invert">
          <p>
            We collect information you provide directly to us, including:
          </p>
          <ul>
            <li><strong>Account Information:</strong> Email address and password when you create an account.</li>
            <li><strong>Writing Samples:</strong> Text you upload to create your personal fingerprint.</li>
            <li><strong>Analysis Data:</strong> Text you submit for AI detection analysis.</li>
            <li><strong>Usage Data:</strong> Information about how you use our service.</li>
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>2. How We Use Your Information</CardTitle>
        </CardHeader>
        <CardContent className="prose dark:prose-invert">
          <p>We use the information we collect to:</p>
          <ul>
            <li>Provide, maintain, and improve our services</li>
            <li>Create and maintain your personal writing fingerprint</li>
            <li>Analyze text for AI detection purposes</li>
            <li>Send you technical notices and support messages</li>
            <li>Respond to your comments and questions</li>
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>3. Data Storage and Security</CardTitle>
        </CardHeader>
        <CardContent className="prose dark:prose-invert">
          <p>
            We implement appropriate technical and organizational measures to protect your personal data:
          </p>
          <ul>
            <li>All data is encrypted in transit using TLS</li>
            <li>Passwords are hashed using bcrypt</li>
            <li>Database access is restricted and logged</li>
            <li>We use local LLM processing (Ollama) - your text never leaves our infrastructure</li>
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>4. Your Rights (GDPR)</CardTitle>
        </CardHeader>
        <CardContent className="prose dark:prose-invert">
          <p>Under GDPR and other data protection laws, you have the right to:</p>
          <ul>
            <li><strong>Access:</strong> Request a copy of all data we hold about you</li>
            <li><strong>Rectification:</strong> Correct inaccurate personal data</li>
            <li><strong>Erasure:</strong> Request deletion of your data ("right to be forgotten")</li>
            <li><strong>Portability:</strong> Receive your data in a machine-readable format</li>
            <li><strong>Restriction:</strong> Request we limit processing of your data</li>
            <li><strong>Objection:</strong> Object to certain processing activities</li>
          </ul>
          <p>
            You can exercise these rights through your account settings or by contacting us.
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>5. Data Retention</CardTitle>
        </CardHeader>
        <CardContent className="prose dark:prose-invert">
          <p>
            We retain your personal data for as long as your account is active or as needed to provide services:
          </p>
          <ul>
            <li>Writing samples: Retained until you delete them or your account</li>
            <li>Analysis results: Automatically deleted after 90 days (configurable)</li>
            <li>Account data: Retained until account deletion</li>
            <li>After account deletion: All data is permanently removed within 30 days</li>
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>6. Third-Party Services</CardTitle>
        </CardHeader>
        <CardContent className="prose dark:prose-invert">
          <p>
            We use the following third-party services:
          </p>
          <ul>
            <li><strong>Ollama:</strong> Local LLM processing (no data leaves your infrastructure)</li>
            <li><strong>PostgreSQL:</strong> Database storage (self-hosted)</li>
            <li><strong>Sentry:</strong> Error tracking (optional, no PII sent)</li>
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>7. Contact Us</CardTitle>
        </CardHeader>
        <CardContent className="prose dark:prose-invert">
          <p>
            If you have any questions about this Privacy Policy or our data practices, please contact us at:
          </p>
          <p>
            <strong>Email:</strong> privacy@ghostwriter.local<br />
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
