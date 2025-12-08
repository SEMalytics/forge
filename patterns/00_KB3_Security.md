00\_KB3\_Security

# KnowledgeForge 3.0: Security Framework

---

title: "Security Framework" module: "00\_Framework" topics: \["security", "authentication", "authorization", "data protection", "API security"\] contexts: \["system security", "access control", "compliance", "threat protection"\] difficulty: "intermediate" related\_sections: \["Implementation", "API Definitions", "Monitoring", "Core"\]

## Core Approach

This module defines the comprehensive security framework for KnowledgeForge 3.0, covering authentication, authorization, data protection, API security, and compliance requirements. Security is integrated at every layer of the system, from agent communications to knowledge storage, ensuring robust protection while maintaining system usability and performance.

## Security Architecture

### Multi-Layer Security Model

1. **Infrastructure Security**  
     
   - Network isolation and segmentation  
   - Encrypted communications (TLS 1.3)  
   - Container security hardening  
   - Infrastructure as Code security scanning

   

2. **Application Security**  
     
   - Secure coding practices  
   - Input validation and sanitization  
   - Output encoding  
   - SQL injection prevention

   

3. **Data Security**  
     
   - Encryption at rest (AES-256)  
   - Encryption in transit (TLS 1.3)  
   - Key management (HSM/KMS)  
   - Data classification and handling

   

4. **Identity and Access Management**  
     
   - Multi-factor authentication  
   - Role-based access control (RBAC)  
   - Attribute-based access control (ABAC)  
   - Session management

## Authentication Framework

### Multi-Method Authentication

```json
{
  "authentication_methods": {
    "api_key": {
      "description": "API key based authentication for service-to-service communication",
      "use_cases": ["workflow_triggers", "agent_communication", "automated_systems"],
      "security_features": [
        "key_rotation",
        "scope_limitation",
        "usage_monitoring",
        "expiration_policies"
      ],
      "implementation": {
        "header": "X-API-Key",
        "format": "kf3_[environment]_[32_chars]_[timestamp]",
        "validation": "hmac_sha256_signature",
        "storage": "encrypted_database"
      }
    },
    "jwt_tokens": {
      "description": "JSON Web Tokens for user session management",
      "use_cases": ["user_sessions", "agent_delegation", "temporary_access"],
      "security_features": [
        "digital_signatures",
        "expiration_times",
        "refresh_tokens",
        "revocation_lists"
      ],
      "implementation": {
        "algorithm": "RS256",
        "issuer": "knowledgeforge.security",
        "audience": "kf3.api",
        "max_lifetime": "24_hours"
      }
    },
    "oauth2": {
      "description": "OAuth 2.0 for third-party integrations",
      "use_cases": ["external_integrations", "sso_systems", "partner_access"],
      "flows": ["authorization_code", "client_credentials", "device_code"],
      "security_features": [
        "pkce_support",
        "state_validation",
        "scope_restrictions",
        "token_introspection"
      ]
    },
    "mutual_tls": {
      "description": "Certificate-based authentication for high-security environments",
      "use_cases": ["critical_systems", "enterprise_integration", "compliance_requirements"],
      "security_features": [
        "certificate_validation",
        "ca_trust_chains",
        "crl_checking",
        "ocsp_stapling"
      ]
    }
  }
}
```

### Authentication Workflow

```javascript
// N8N Authentication Workflow
{
  "name": "Authentication Validation",
  "nodes": [
    {
      "parameters": {
        "functionCode": `
// Multi-method authentication validator
const request = $json;
const authHeader = request.headers?.authorization || '';
const apiKey = request.headers?.['x-api-key'] || '';
const clientCert = request.headers?.['x-client-cert'] || '';

const authResult = {
  method: null,
  valid: false,
  identity: null,
  permissions: [],
  metadata: {}
};

// Determine authentication method
if (apiKey) {
  authResult.method = 'api_key';
  const keyValidation = validateApiKey(apiKey);
  authResult.valid = keyValidation.valid;
  authResult.identity = keyValidation.identity;
  authResult.permissions = keyValidation.permissions;
} else if (authHeader.startsWith('Bearer ')) {
  authResult.method = 'jwt';
  const token = authHeader.substring(7);
  const tokenValidation = validateJwtToken(token);
  authResult.valid = tokenValidation.valid;
  authResult.identity = tokenValidation.identity;
  authResult.permissions = tokenValidation.permissions;
} else if (clientCert) {
  authResult.method = 'mutual_tls';
  const certValidation = validateClientCertificate(clientCert);
  authResult.valid = certValidation.valid;
  authResult.identity = certValidation.identity;
  authResult.permissions = certValidation.permissions;
}

function validateApiKey(key) {
  // API key validation logic
  const keyPattern = /^kf3_([a-z]+)_([a-f0-9]{32})_(\d+)$/;
  const match = key.match(keyPattern);
  
  if (!match) {
    return { valid: false, reason: 'invalid_format' };
  }
  
  const [, environment, keyHash, timestamp] = match;
  
  // Check key age
  const keyAge = Date.now() - parseInt(timestamp);
  const maxAge = 90 * 24 * 60 * 60 * 1000; // 90 days
  
  if (keyAge > maxAge) {
    return { valid: false, reason: 'expired' };
  }
  
  // Lookup key in database (simulated)
  const keyRecord = lookupApiKey(keyHash);
  if (!keyRecord) {
    return { valid: false, reason: 'not_found' };
  }
  
  if (keyRecord.revoked) {
    return { valid: false, reason: 'revoked' };
  }
  
  return {
    valid: true,
    identity: {
      type: 'service',
      id: keyRecord.service_id,
      name: keyRecord.service_name
    },
    permissions: keyRecord.scopes || []
  };
}

function validateJwtToken(token) {
  try {
    // JWT validation logic (simplified)
    const decoded = verifyJwtSignature(token);
    
    // Check expiration
    if (decoded.exp && decoded.exp < Date.now() / 1000) {
      return { valid: false, reason: 'expired' };
    }
    
    // Check revocation
    if (isTokenRevoked(decoded.jti)) {
      return { valid: false, reason: 'revoked' };
    }
    
    return {
      valid: true,
      identity: {
        type: 'user',
        id: decoded.sub,
        name: decoded.name,
        email: decoded.email
      },
      permissions: decoded.scope?.split(' ') || []
    };
  } catch (error) {
    return { valid: false, reason: 'invalid_signature' };
  }
}

function validateClientCertificate(cert) {
  // Certificate validation logic
  const certData = parseCertificate(cert);
  
  if (!certData) {
    return { valid: false, reason: 'invalid_certificate' };
  }
  
  // Verify certificate chain
  if (!verifyCertificateChain(certData)) {
    return { valid: false, reason: 'invalid_chain' };
  }
  
  // Check revocation
  if (isCertificateRevoked(certData.serialNumber)) {
    return { valid: false, reason: 'revoked' };
  }
  
  return {
    valid: true,
    identity: {
      type: 'system',
      id: certData.subject.CN,
      organization: certData.subject.O
    },
    permissions: extractPermissionsFromCert(certData)
  };
}

// Mock functions (would be implemented with actual crypto libraries)
function lookupApiKey(hash) { return { service_id: 'test', service_name: 'Test Service', scopes: ['read'] }; }
function verifyJwtSignature(token) { return JSON.parse(atob(token.split('.')[1])); }
function isTokenRevoked(jti) { return false; }
function parseCertificate(cert) { return { subject: { CN: 'test', O: 'TestOrg' }, serialNumber: '123' }; }
function verifyCertificateChain(cert) { return true; }
function isCertificateRevoked(serial) { return false; }
function extractPermissionsFromCert(cert) { return ['system:read']; }

return { json: authResult };
`
      },
      "id": "validate_auth",
      "name": "Validate Authentication",
      "type": "n8n-nodes-base.function",
      "position": [250, 300]
    },
    {
      "parameters": {
        "conditions": {
          "boolean": [
            {
              "value1": "={{$json.valid}}",
              "value2": true
            }
          ]
        }
      },
      "id": "auth_check",
      "name": "Authentication Valid?",
      "type": "n8n-nodes-base.if",
      "position": [430, 300]
    },
    {
      "parameters": {
        "functionCode": `
// Log authentication failure
const authResult = $node['Validate Authentication'].json;
const request = $node['Validate Authentication'].json;

const securityEvent = {
  timestamp: new Date().toISOString(),
  event_type: 'authentication_failure',
  source_ip: request.headers?.['x-forwarded-for'] || 'unknown',
  user_agent: request.headers?.['user-agent'] || 'unknown',
  auth_method: authResult.method,
  failure_reason: authResult.reason || 'unknown',
  request_path: request.path || '/',
  severity: 'medium'
};

// Enhanced threat detection
if (authResult.reason === 'brute_force_detected') {
  securityEvent.severity = 'high';
  securityEvent.action_required = 'ip_blocking';
}

return {
  json: {
    status: 'unauthorized',
    error: 'Authentication failed',
    code: 401,
    security_event: securityEvent
  }
};
`
      },
      "id": "auth_failure",
      "name": "Authentication Failure",
      "type": "n8n-nodes-base.function",
      "position": [610, 400]
    },
    {
      "parameters": {
        "functionCode": `
// Log successful authentication and set context
const authResult = $node['Validate Authentication'].json;

const securityEvent = {
  timestamp: new Date().toISOString(),
  event_type: 'authentication_success',
  identity: authResult.identity,
  auth_method: authResult.method,
  permissions: authResult.permissions,
  session_id: generateSessionId()
};

function generateSessionId() {
  return 'sess_' + Math.random().toString(36).substr(2, 16) + '_' + Date.now();
}

return {
  json: {
    status: 'authenticated',
    identity: authResult.identity,
    permissions: authResult.permissions,
    session_id: securityEvent.session_id,
    security_event: securityEvent
  }
};
`
      },
      "id": "auth_success",
      "name": "Authentication Success",
      "type": "n8n-nodes-base.function",
      "position": [610, 200]
    }
  ]
}
```

## Authorization Framework

### Role-Based Access Control (RBAC)

```json
{
  "rbac_model": {
    "roles": {
      "system_admin": {
        "description": "Full system administration access",
        "permissions": [
          "system:*",
          "knowledge:*",
          "workflow:*",
          "agent:*",
          "security:*"
        ],
        "restrictions": {
          "ip_whitelist": ["admin_networks"],
          "time_restrictions": "business_hours",
          "mfa_required": true
        }
      },
      "knowledge_manager": {
        "description": "Knowledge base management and curation",
        "permissions": [
          "knowledge:create",
          "knowledge:update",
          "knowledge:delete",
          "knowledge:read",
          "workflow:read",
          "agent:configure"
        ],
        "restrictions": {
          "content_domains": ["approved_domains"],
          "bulk_operations": "limited"
        }
      },
      "agent_operator": {
        "description": "Agent configuration and monitoring",
        "permissions": [
          "agent:create",
          "agent:update",
          "agent:read",
          "workflow:execute",
          "knowledge:read"
        ],
        "restrictions": {
          "agent_types": ["standard", "utility"],
          "resource_limits": "standard"
        }
      },
      "workflow_developer": {
        "description": "Workflow development and testing",
        "permissions": [
          "workflow:create",
          "workflow:update",
          "workflow:read",
          "workflow:test",
          "knowledge:read"
        ],
        "restrictions": {
          "environments": ["development", "staging"],
          "resource_limits": "development"
        }
      },
      "knowledge_user": {
        "description": "Standard knowledge access and consumption",
        "permissions": [
          "knowledge:read",
          "agent:interact",
          "search:execute"
        ],
        "restrictions": {
          "rate_limits": "standard",
          "content_filters": "user_appropriate"
        }
      },
      "api_consumer": {
        "description": "Programmatic API access for integrations",
        "permissions": [
          "api:knowledge:read",
          "api:search:execute",
          "api:agent:interact"
        ],
        "restrictions": {
          "rate_limits": "api_standard",
          "scope_limitations": "read_only"
        }
      }
    },
    "permission_hierarchy": {
      "system": ["admin", "configure", "monitor", "audit"],
      "knowledge": ["create", "update", "delete", "read", "publish"],
      "workflow": ["create", "update", "delete", "read", "execute", "test"],
      "agent": ["create", "update", "delete", "read", "configure", "interact"],
      "search": ["execute", "configure", "analyze"],
      "api": ["access", "configure", "monitor"]
    }
  }
}
```

### Attribute-Based Access Control (ABAC)

```javascript
// ABAC Policy Engine
{
  "name": "ABAC Authorization Check",
  "nodes": [
    {
      "parameters": {
        "functionCode": `
// Attribute-based access control evaluation
const request = $json.request;
const identity = $json.identity;
const resource = $json.resource;
const action = $json.action;
const environment = $json.environment || {};

const decision = evaluateAbacPolicy(identity, resource, action, environment);

function evaluateAbacPolicy(subject, resource, action, env) {
  const policies = loadApplicablePolicies(resource.type, action);
  
  for (const policy of policies) {
    const result = evaluatePolicy(policy, subject, resource, action, env);
    
    if (result.effect === 'deny') {
      return {
        decision: 'deny',
        reason: result.reason,
        policy: policy.id
      };
    }
    
    if (result.effect === 'permit') {
      return {
        decision: 'permit',
        conditions: result.conditions,
        policy: policy.id
      };
    }
  }
  
  // Default deny
  return {
    decision: 'deny',
    reason: 'no_applicable_policy'
  };
}

function loadApplicablePolicies(resourceType, action) {
  // Load policies from policy store
  const allPolicies = [
    {
      id: 'knowledge_access_policy',
      target: {
        resource_types: ['knowledge_module'],
        actions: ['read', 'search']
      },
      rules: [
        {
          condition: 'subject.role in ["knowledge_user", "knowledge_manager", "system_admin"]',
          effect: 'permit'
        },
        {
          condition: 'resource.classification == "restricted" and subject.clearance < "secret"',
          effect: 'deny',
          reason: 'insufficient_clearance'
        }
      ]
    },
    {
      id: 'workflow_execution_policy',
      target: {
        resource_types: ['workflow'],
        actions: ['execute']
      },
      rules: [
        {
          condition: 'subject.role in ["workflow_developer", "agent_operator", "system_admin"]',
          effect: 'permit'
        },
        {
          condition: 'environment.time not in business_hours and resource.requires_approval',
          effect: 'deny',
          reason: 'outside_business_hours'
        }
      ]
    },
    {
      id: 'agent_interaction_policy',
      target: {
        resource_types: ['agent'],
        actions: ['interact', 'configure']
      },
      rules: [
        {
          condition: 'action == "interact" and subject.role in ["knowledge_user", "agent_operator", "system_admin"]',
          effect: 'permit'
        },
        {
          condition: 'action == "configure" and subject.role in ["agent_operator", "system_admin"]',
          effect: 'permit'
        },
        {
          condition: 'resource.agent_type == "critical" and subject.role != "system_admin"',
          effect: 'deny',
          reason: 'critical_agent_access_restricted'
        }
      ]
    }
  ];
  
  return allPolicies.filter(policy => 
    policy.target.resource_types.includes(resourceType) &&
    policy.target.actions.includes(action)
  );
}

function evaluatePolicy(policy, subject, resource, action, env) {
  for (const rule of policy.rules) {
    if (evaluateCondition(rule.condition, subject, resource, action, env)) {
      return {
        effect: rule.effect,
        reason: rule.reason,
        conditions: rule.conditions
      };
    }
  }
  
  return { effect: 'not_applicable' };
}

function evaluateCondition(condition, subject, resource, action, env) {
  // Simplified condition evaluation
  // In practice, this would use a proper expression evaluator
  
  const context = {
    subject,
    resource,
    action,
    environment: env,
    business_hours: isBusinessHours(env.time)
  };
  
  // Replace variables in condition
  let evaluatedCondition = condition;
  Object.entries(context).forEach(([key, value]) => {
    if (typeof value === 'object') {
      Object.entries(value).forEach(([subKey, subValue]) => {
        evaluatedCondition = evaluatedCondition.replace(
          new RegExp(\`\${key}\\.\${subKey}\`, 'g'),
          JSON.stringify(subValue)
        );
      });
    }
  });
  
  // Simple evaluation (would use proper expression parser)
  try {
    return eval(evaluatedCondition.replace(/in \\[([^\\]]+)\\]/g, (match, list) => {
      return \`.includes(\${list})\`;
    }));
  } catch (error) {
    console.error('Condition evaluation error:', error);
    return false;
  }
}

function isBusinessHours(time) {
  if (!time) return true; // Default to business hours if no time provided
  const hour = new Date(time).getHours();
  return hour >= 9 && hour <= 17; // 9 AM to 5 PM
}

return { json: decision };
`
      },
      "id": "evaluate_abac",
      "name": "Evaluate ABAC Policy",
      "type": "n8n-nodes-base.function",
      "position": [250, 300]
    }
  ]
}
```

## Data Protection and Privacy

### Data Classification

```json
{
  "data_classification": {
    "levels": {
      "public": {
        "description": "Information that can be freely shared",
        "examples": ["documentation", "public APIs", "marketing materials"],
        "protection": {
          "encryption": "optional",
          "access_control": "none",
          "audit_logging": "basic"
        }
      },
      "internal": {
        "description": "Information for internal use within organization",
        "examples": ["internal processes", "employee directories", "project plans"],
        "protection": {
          "encryption": "recommended",
          "access_control": "role_based",
          "audit_logging": "standard"
        }
      },
      "confidential": {
        "description": "Sensitive information requiring protection",
        "examples": ["customer data", "financial information", "strategic plans"],
        "protection": {
          "encryption": "required",
          "access_control": "attribute_based",
          "audit_logging": "detailed"
        }
      },
      "restricted": {
        "description": "Highly sensitive information with strict access controls",
        "examples": ["security keys", "personal data", "trade secrets"],
        "protection": {
          "encryption": "required_with_key_management",
          "access_control": "explicit_authorization",
          "audit_logging": "comprehensive"
        }
      }
    }
  }
}
```

### Encryption Framework

```javascript
// Encryption service workflow
{
  "name": "Data Encryption Service",
  "nodes": [
    {
      "parameters": {
        "functionCode": `
// Data encryption/decryption service
const operation = $json.operation; // 'encrypt' or 'decrypt'
const data = $json.data;
const classification = $json.classification;
const context = $json.context || {};

const result = {
  operation,
  success: false,
  data: null,
  metadata: {}
};

try {
  const encryptionConfig = getEncryptionConfig(classification);
  
  if (operation === 'encrypt') {
    result.data = encryptData(data, encryptionConfig, context);
    result.metadata = {
      algorithm: encryptionConfig.algorithm,
      keyId: encryptionConfig.keyId,
      encryptedAt: new Date().toISOString()
    };
  } else if (operation === 'decrypt') {
    result.data = decryptData(data, encryptionConfig, context);
    result.metadata = {
      decryptedAt: new Date().toISOString(),
      keyId: encryptionConfig.keyId
    };
  }
  
  result.success = true;
} catch (error) {
  result.error = {
    message: error.message,
    code: 'ENCRYPTION_ERROR',
    timestamp: new Date().toISOString()
  };
}

function getEncryptionConfig(classification) {
  const configs = {
    'public': {
      algorithm: 'none',
      keyId: null
    },
    'internal': {
      algorithm: 'AES-256-GCM',
      keyId: 'kf3-internal-key-01',
      keySource: 'local'
    },
    'confidential': {
      algorithm: 'AES-256-GCM',
      keyId: 'kf3-confidential-key-01',
      keySource: 'kms'
    },
    'restricted': {
      algorithm: 'AES-256-GCM',
      keyId: 'kf3-restricted-key-01',
      keySource: 'hsm'
    }
  };
  
  return configs[classification] || configs['internal'];
}

function encryptData(data, config, context) {
  if (config.algorithm === 'none') return data;
  
  // Simulate encryption (would use actual crypto library)
  const key = retrieveKey(config.keyId, config.keySource);
  const iv = generateIV();
  
  // In practice, use Node.js crypto module or similar
  const encrypted = {
    ciphertext: btoa(JSON.stringify(data)), // Simulated encryption
    iv: iv,
    tag: 'simulated_auth_tag',
    algorithm: config.algorithm
  };
  
  return encrypted;
}

function decryptData(encryptedData, config, context) {
  if (config.algorithm === 'none') return encryptedData;
  
  // Simulate decryption
  const key = retrieveKey(config.keyId, config.keySource);
  
  // Verify authentication tag
  if (!verifyAuthTag(encryptedData.tag, encryptedData.ciphertext)) {
    throw new Error('Authentication verification failed');
  }
  
  // Decrypt data
  const decrypted = JSON.parse(atob(encryptedData.ciphertext));
  return decrypted;
}

function retrieveKey(keyId, source) {
  // Key retrieval from various sources
  const mockKeys = {
    'kf3-internal-key-01': 'internal_key_data',
    'kf3-confidential-key-01': 'confidential_key_data',
    'kf3-restricted-key-01': 'restricted_key_data'
  };
  
  return mockKeys[keyId] || 'default_key';
}

function generateIV() {
  return Math.random().toString(36).substr(2, 16);
}

function verifyAuthTag(tag, ciphertext) {
  // Simulate authentication tag verification
  return tag === 'simulated_auth_tag';
}

return { json: result };
`
      },
      "id": "encryption_service",
      "name": "Encryption Service",
      "type": "n8n-nodes-base.function"
    }
  ]
}
```

## API Security

### API Gateway Security

```javascript
// API security middleware workflow
{
  "name": "API Security Gateway",
  "nodes": [
    {
      "parameters": {
        "functionCode": `
// Comprehensive API security checks
const request = $json;

const securityChecks = {
  rateLimit: checkRateLimit(request),
  inputValidation: validateInput(request),
  sqlInjection: detectSqlInjection(request),
  xss: detectXss(request),
  authorization: checkAuthorization(request),
  threatDetection: detectThreats(request)
};

const result = {
  allowed: true,
  checks: securityChecks,
  riskScore: calculateRiskScore(securityChecks),
  actions: []
};

// Evaluate security checks
Object.entries(securityChecks).forEach(([check, result]) => {
  if (!result.passed) {
    result.allowed = false;
    result.actions.push(result.action || 'block_request');
  }
});

function checkRateLimit(req) {
  const clientId = req.headers?.['x-client-id'] || req.ip || 'unknown';
  const endpoint = req.path || '/';
  const timeWindow = 60; // 1 minute
  
  // Simulate rate limit check
  const requestCount = getCurrentRequestCount(clientId, endpoint, timeWindow);
  const limit = getRateLimit(req.identity?.role || 'anonymous');
  
  return {
    passed: requestCount <= limit,
    details: {
      current: requestCount,
      limit: limit,
      window: timeWindow
    },
    action: 'rate_limit_exceeded'
  };
}

function validateInput(req) {
  const validationRules = {
    maxBodySize: 10 * 1024 * 1024, // 10MB
    allowedContentTypes: ['application/json', 'text/plain', 'multipart/form-data'],
    maxHeaderSize: 8192
  };
  
  const violations = [];
  
  // Check body size
  if (req.body && JSON.stringify(req.body).length > validationRules.maxBodySize) {
    violations.push('body_too_large');
  }
  
  // Check content type
  const contentType = req.headers?.['content-type']?.split(';')[0];
  if (contentType && !validationRules.allowedContentTypes.includes(contentType)) {
    violations.push('invalid_content_type');
  }
  
  // Check header size
  const headerSize = JSON.stringify(req.headers || {}).length;
  if (headerSize > validationRules.maxHeaderSize) {
    violations.push('headers_too_large');
  }
  
  return {
    passed: violations.length === 0,
    violations: violations,
    action: 'input_validation_failed'
  };
}

function detectSqlInjection(req) {
  const sqlPatterns = [
    /('|(\\-\\-)|(;)|(\\|)|(\\*)|(%))/i,
    /(union|select|insert|delete|update|drop|create|alter|exec|execute)/i,
    /(script|javascript|vbscript|onload|onerror)/i
  ];
  
  const testStrings = [];
  
  // Check query parameters
  if (req.query) {
    Object.values(req.query).forEach(value => {
      if (typeof value === 'string') testStrings.push(value);
    });
  }
  
  // Check body parameters
  if (req.body && typeof req.body === 'object') {
    const bodyStr = JSON.stringify(req.body);
    testStrings.push(bodyStr);
  }
  
  const suspiciousPatterns = [];
  testStrings.forEach(str => {
    sqlPatterns.forEach((pattern, index) => {
      if (pattern.test(str)) {
        suspiciousPatterns.push({
          pattern: index,
          value: str.substring(0, 100) // Truncate for logging
        });
      }
    });
  });
  
  return {
    passed: suspiciousPatterns.length === 0,
    patterns: suspiciousPatterns,
    action: 'sql_injection_detected'
  };
}

function detectXss(req) {
  const xssPatterns = [
    /<script[^>]*>.*?<\\/script>/gi,
    /<iframe[^>]*>.*?<\\/iframe>/gi,
    /javascript:/gi,
    /on\\w+\\s*=/gi,
    /<\\w+[^>]*\\s(on\\w+|href|src)\\s*=/gi
  ];
  
  const testStrings = [];
  
  // Collect strings to test
  if (req.query) {
    Object.values(req.query).forEach(value => {
      if (typeof value === 'string') testStrings.push(value);
    });
  }
  
  if (req.body && typeof req.body === 'string') {
    testStrings.push(req.body);
  }
  
  const xssAttempts = [];
  testStrings.forEach(str => {
    xssPatterns.forEach((pattern, index) => {
      if (pattern.test(str)) {
        xssAttempts.push({
          pattern: index,
          value: str.substring(0, 100)
        });
      }
    });
  });
  
  return {
    passed: xssAttempts.length === 0,
    attempts: xssAttempts,
    action: 'xss_detected'
  };
}

function checkAuthorization(req) {
  // This would integrate with the ABAC system
  const requiredPermission = deriveRequiredPermission(req.method, req.path);
  const userPermissions = req.identity?.permissions || [];
  
  const hasPermission = userPermissions.some(permission => 
    permissionMatches(permission, requiredPermission)
  );
  
  return {
    passed: hasPermission,
    required: requiredPermission,
    available: userPermissions,
    action: 'authorization_failed'
  };
}

function detectThreats(req) {
  const threats = [];
  
  // Check for known malicious IPs
  const clientIp = req.headers?.['x-forwarded-for'] || req.ip;
  if (isKnownMaliciousIp(clientIp)) {
    threats.push({
      type: 'malicious_ip',
      severity: 'high',
      details: { ip: clientIp }
    });
  }
  
  // Check for suspicious user agent
  const userAgent = req.headers?.['user-agent'] || '';
  if (isSuspiciousUserAgent(userAgent)) {
    threats.push({
      type: 'suspicious_user_agent',
      severity: 'medium',
      details: { userAgent: userAgent.substring(0, 100) }
    });
  }
  
  // Check for rapid successive requests (potential DOS)
  if (hasRapidRequests(clientIp)) {
    threats.push({
      type: 'potential_dos',
      severity: 'high',
      details: { ip: clientIp }
    });
  }
  
  return {
    passed: threats.length === 0,
    threats: threats,
    action: threats.length > 0 ? 'threat_detected' : null
  };
}

function calculateRiskScore(checks) {
  let score = 0;
  const weights = {
    rateLimit: 20,
    inputValidation: 15,
    sqlInjection: 30,
    xss: 25,
    authorization: 35,
    threatDetection: 40
  };
  
  Object.entries(checks).forEach(([check, result]) => {
    if (!result.passed) {
      score += weights[check] || 10;
    }
  });
  
  return Math.min(score, 100);
}

// Helper functions (simplified implementations)
function getCurrentRequestCount(clientId, endpoint, window) { return Math.floor(Math.random() * 100); }
function getRateLimit(role) { 
  const limits = { 'anonymous': 10, 'user': 100, 'admin': 1000 };
  return limits[role] || 10;
}
function deriveRequiredPermission(method, path) {
  if (path.startsWith('/api/knowledge')) return 'knowledge:read';
  if (path.startsWith('/api/workflow')) return 'workflow:execute';
  return 'api:access';
}
function permissionMatches(userPerm, required) {
  return userPerm === required || userPerm.endsWith(':*');
}
function isKnownMaliciousIp(ip) { return false; } // Would check threat intelligence feeds
function isSuspiciousUserAgent(ua) { return ua.includes('sqlmap') || ua.includes('nmap'); }
function hasRapidRequests(ip) { return false; } // Would check request frequency

return { json: result };
`
      },
      "id": "api_security_check",
      "name": "API Security Check",
      "type": "n8n-nodes-base.function",
      "position": [250, 300]
    }
  ]
}
```

