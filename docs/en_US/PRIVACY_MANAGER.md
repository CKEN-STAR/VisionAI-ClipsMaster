# Privacy Manager

The Privacy Manager is a module designed to detect, anonymize, and redact personally identifiable information (PII) in text data. It provides robust functionality for privacy protection in the VisionAI-ClipsMaster application.

## Features

- **PII Detection**: Identify various types of personal information in text
- **Anonymization**: Replace PII with placeholder tokens
- **Redaction**: Mask PII with replacement characters (e.g., asterisks)
- **JSON Support**: Extract and process PII from JSON structures
- **Statistics**: Track and report on detected PII

## Supported PII Types

The Privacy Manager can detect the following types of personally identifiable information:

| PII Type | Description | Example Pattern |
|----------|-------------|-----------------|
| Phone | Chinese mobile phone numbers | 13812345678 |
| Email | Email addresses | user@example.com |
| ID Card | Chinese national ID numbers | 110101199001011234 |
| Credit Card | Credit card numbers | 1234 5678 9012 3456 |
| Address | Simple address patterns | 北京市海淀区清华园路1号 |
| Passport | Passport numbers | G12345678 |
| IP Address | IPv4 addresses | 192.168.1.1 |
| Name | Simple name patterns | 张先生, 李女士 |

## Usage Examples

### Basic PII Detection

```python
from src.utils.privacy_manager import PrivacyManager

# Initialize the privacy manager
pm = PrivacyManager()

# Sample text with PII
text = "Please contact Zhang San at 13800138000 or zhangsan@example.com for assistance."

# Detect PII
results = pm.detect_pii(text)
print(f"Found {len(results)} PII instances")
```

### Text Anonymization

```python
from src.utils.privacy_manager import PrivacyManager

pm = PrivacyManager()

# Sample text with PII
text = "Customer Li Si lives at 北京市海淀区清华园路1号 and uses card 1234 5678 9012 3456."

# Anonymize the text
anonymized = pm.anonymize_pii(text)
print(anonymized)
# Output: "Customer Li Si lives at [地址信息] and uses card [信用卡号]."
```

### PII Redaction

```python
from src.utils.privacy_manager import PrivacyManager

pm = PrivacyManager()

# Sample text with PII
text = "My email is user@example.com and my phone is 13800138000."

# Redact PII with asterisks
redacted = pm.redact_pii(text)
print(redacted)
# Output: "My email is ****************** and my phone is ***********."

# Redact PII with a custom character
redacted_custom = pm.redact_pii(text, replacement_char="X")
print(redacted_custom)
# Output: "My email is XXXXXXXXXXXXXXXX and my phone is XXXXXXXXXXX."
```

### Processing JSON Data

```python
from src.utils.privacy_manager import PrivacyManager

pm = PrivacyManager()

# Sample JSON with PII
json_data = {
    "user": {
        "name": "Wang Wu先生",
        "contact": {
            "email": "wangwu@example.com",
            "phone": "13900139000"
        },
        "address": "上海市浦东新区张江高科技园区"
    },
    "payment": {
        "card_number": "9876 5432 1098 7654"
    }
}

# Anonymize JSON
anonymized_json = pm.anonymize_pii(json_data)
print(anonymized_json)
```

### Getting PII Statistics

```python
from src.utils.privacy_manager import PrivacyManager

pm = PrivacyManager()

# Process multiple texts with PII
texts = [
    "Contact Zhang San at 13800138000",
    "Email to zhangsan@example.com",
    "ID: 110101199001011234",
    "Card: 1234 5678 9012 3456"
]

for text in texts:
    pm.anonymize_pii(text)

# Get statistics
stats = pm.get_pii_statistics()
print(stats)
```

## Integration with Content Validator

The Privacy Manager module can be integrated with the Content Validator to provide comprehensive content screening:

```python
from src.utils.privacy_manager import PrivacyManager
from src.core.content_validator import ContentValidator

pm = PrivacyManager()
cv = ContentValidator()

def process_user_content(content):
    # First check for sensitive content
    sensitivity_result = cv.check_content(content)
    
    # Then anonymize any PII
    if sensitivity_result["is_safe"]:
        processed_content = pm.anonymize_pii(content)
        return {
            "is_safe": True,
            "processed_content": processed_content
        }
    else:
        return {
            "is_safe": False,
            "reason": sensitivity_result["reason"]
        }
```

## Technical Notes

- The Privacy Manager uses regular expressions for pattern matching
- Detected PII is tracked using MD5 hashes to avoid duplicates
- Anonymization maintains consistency by using the same replacement for identical PII instances
- For processing large volumes of text, consider performance implications of regex matching 