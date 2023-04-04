# Secrets Detection

NB Defense scans for any secrets or authentication information(such as passwords or tokens) that may be present in a notebook.

To enable this we have built a wrapper around Yelp's [detect-secrets](https://github.com/Yelp/detect-secrets) library, porting its capabilities to check the input and output cells of your notebooks.

!!! warning

    Before you begin scanning for secrets, please execute all code inside the notebook that you would like scanned. This plugin does not execute code, and will only scan output for secrets if it exists in the notebook. 

## Supported detect-secrets Plugins

Following is a list of the different types of authentication information that is scanned for by the NB Defense:

1. API keys and tokens - Application Programming Interface (API) keys and tokens will be detected by NB Defense scan. They are typically used to authenticate a calling program communicating with an API.
2. Amazon Web Services (AWS) key - AWS key is used to gain access to all the AWS resources.
3. Azure storage key - Azure storage key is used to authorize access to data in Azure storage account.
4. Basic authentication - HTTP web browser authentication is usually undertaken using a username and password when making a request such as accessing email.
5. Cloudant detector - The Cloudant detector is a unique identifier for a document in a database.
6. Discord bot token - The Artificial Intelligence (AI) driven bots that can automate tasks for moderating server.
7. GitHub token - GitHub token is an alternative to password when using the GitHub API or the command line for accessing GitHub resources.
8. Base64 High Entropy String - Strings with high entropy that appear to be Base64 encoded.
9. Hex High Entropy String - Strings with high entropy that appear to be in a hexadecimal format.
10. IBM Cloud Identity and Access Management
11. IBM Hash-based Message Authentication Code (HMAC) - IBM HMAC credentials consist of an Access Key and Secret Key paired for use with S3-compatible tools and libraries that require authentication.
12. JSON Web Token - JSON Web Tokens (JWT) are an open, industry standard RFC 7519 method for representing claims securely between two parties.
13. Keywords - Keywords are used for finding tokens and passwords such as 'The password is: **\***'. The word password is a keyword since it gives context.
14. Mailchimp - Mailchimp is used by marketers for promotional emails. NB Defense detection scans for login information for Mailchimp.
15. Node Package Manager (NPM) - NPM detection scans for login information for NPM.
16. Private Key - Private key detection is used for detecting any private or secret keys that could be used for data encryption.
17. SendGrid - SendGrid is an email marketing provider used for promotional emails.
18. Slack - Slack is a messaging application used by businesses for connecting their team.
19. Softlayer - IBM SoftLayer is a public cloud computing platform that offers a range of services, such as compute, storage, and application development.
20. SquareOAuth - The OAuth allows for sharing of information between services without exposing a password.
21. Stripe - Stripe enables online payment processing for online businesses.
22. Twilio - Twilio is a customer engagement platform which is programmable.

### Plugin Options

There are a few plugins that have their own options:

| Plugin                    | Option            | Description                                                                                                                                                                                        |
| ------------------------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Base64HighEntropyString` | `limit`           | Sets the [Shannon entropy](https://rzepsky.medium.com/hunting-for-secrets-with-the-dumpsterdiver-93d38a9cd4c1) limit for high entropy strings. Value must be between 0.0 and 8.0, defaults to 4.5. |
| `HexHighEntropyString`    | `limit`           | Sets the [Shannon entropy](https://rzepsky.medium.com/hunting-for-secrets-with-the-dumpsterdiver-93d38a9cd4c1) limit for high entropy strings. Value must be between 0.0 and 8.0, defaults to 3.0. |
| `KeywordDetector`         | `keyword_exclude` | Specify a regex string to exclude certain strings from the secrets scan.                                                                                                                           |
