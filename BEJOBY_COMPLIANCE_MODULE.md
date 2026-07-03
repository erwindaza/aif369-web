# Bejoby Recruitment Agent - Privacy & Compliance Module

**Status**: Design Phase
**Urgency**: HIGH (Ley 21.719 vigente Dec 1, 2026)
**Data at risk**: CVs con datos personales de candidatos

---

## CONTEXTO & RIESGOS

### Datos Actuales (NO COMPLIANCE):
```
Email: edaza@bejoby.com (Zoho Mail)
└─ CVs de candidatos (datos personales)
   ├─ Nombres completos
   ├─ Emails personales
   ├─ Teléfonos
   ├─ Direcciones
   ├─ Historial laboral
   └─ Información sensible

Riesgo: Almacenamiento sin encriptación, sin consentimiento documentado
Multa potencial: 5,000-20,000 UTM (~$335k-$1.3M USD)
```

### Requierimientos Legales (Ley 21.719):
```
✅ MUST HAVE:
├─ Consentimiento explícito de candidatos
├─ Política de Privacidad clara
├─ Encriptación en reposo + tránsito
├─ Derechos ARCO implementados
├─ Audit logs de acceso
├─ Retención máxima de 2 años
├─ DPO (Data Protection Officer) designado
└─ Breach notification protocol (72 horas)

❌ CURRENT STATE:
└─ Nada de lo anterior
```

---

## ARQUITECTURA: Bejoby Recruitment Agent (Privacy-by-Design)

```
┌─────────────────────────────────────────────────────────┐
│           Bejoby.com Job Portal                         │
│  (Standalone, separate from AIF369.com)                │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────▼──────────────┐
        │  Consent Layer              │
        │  (GDPR/Ley 21.719)          │
        │                              │
        │  ✓ CV upload consent        │
        │  ✓ Processing consent       │
        │  ✓ Data retention consent   │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │  Encryption Layer           │
        │  (At rest + in transit)     │
        │                              │
        │  ✓ TLS 1.3                  │
        │  ✓ AES-256 encryption       │
        │  ✓ Key rotation             │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────────────────────┐
        │  Data Minimization Layer                    │
        │  (Only extract needed fields)               │
        │                                              │
        │  Raw CV (delete after processing)           │
        │    ↓                                         │
        │  Extract to structured (secure storage)     │
        │    ├─ name, email, phone                   │
        │    ├─ work_experience, education           │
        │    ├─ skills                               │
        │    └─ consent_timestamp, consent_id        │
        └──────────────┬──────────────────────────────┘
                       │
        ┌──────────────▼──────────────┐
        │  Recruitment Agent          │
        │  (LangGraph on Profile 360) │
        │                              │
        │  ✓ CV parsing               │
        │  ✓ Skills matching          │
        │  ✓ Job recommendations      │
        │  ✓ Candidate scoring        │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────┐
        │  Audit & Compliance Layer   │
        │                              │
        │  ✓ Access logs              │
        │  ✓ ARCO requests tracking   │
        │  ✓ Consent audit trail      │
        │  ✓ Breach notification      │
        └──────────────┬──────────────┘
                       │
        ┌──────────────▼──────────────────────────────┐
        │  Secure Storage (Encrypted)                │
        │                                              │
        │  Bejoby DB (separate from AIF369)          │
        │  ├─ candidate_profiles (structured)        │
        │  ├─ consent_records                        │
        │  ├─ audit_logs                             │
        │  ├─ arco_requests                          │
        │  └─ access_history                         │
        └──────────────────────────────────────────────┘
```

---

## DATA CLASSIFICATION & HANDLING

### Datos Personales (HIGH SENSITIVITY):
```yaml
Candidate Names:
  storage: encrypted_db
  access: only_hired_staff + audit_log
  retention: 2_years_max
  encryption: AES-256

Contact Info (Email/Phone):
  storage: encrypted_db
  access: only_if_consent_provided
  retention: 2_years_max
  
Work History:
  storage: encrypted_db
  access: job_matching_only
  retention: 2_years_max

⚠️ Special Category (if present):
  medical_history: DO_NOT_STORE
  criminal_record: DO_NOT_STORE
  disability: only_if_shared_voluntarily + audit
```

---

## COMPLIANCE IMPLEMENTATION

### 1. Consent Management (CRITICAL)

```python
# api/consent.py
class ConsentManager:
    def create_consent_record(self, candidate_email: str, cv_file):
        """
        MUST collect:
        1. Explicit consent to process CV
        2. Purpose (job matching only)
        3. Retention period (2 years)
        4. Data processing disclosure
        5. ARCO rights explanation
        """
        consent = {
            'consent_id': uuid.uuid4(),
            'candidate_email': candidate_email,
            'timestamp': datetime.utcnow(),
            'version': 'ley_21719_v1',
            'consents': {
                'cv_processing': True/False,
                'skill_matching': True/False,
                'marketing_emails': True/False,  # Oposición right
                'data_sharing': True/False,  # With HR tools
            },
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'expires_at': datetime.utcnow() + timedelta(days=730),
        }
        
        # Audit: log this immediately
        audit_log.insert(consent)
        
        return consent
```

### 2. Encryption at Rest

```python
# utils/encryption.py
from cryptography.fernet import Fernet

class DataEncryption:
    def __init__(self, key: str):
        self.cipher = Fernet(key)
    
    def encrypt_cv(self, file_content: bytes) -> bytes:
        """Encrypt CV before storing"""
        return self.cipher.encrypt(file_content)
    
    def decrypt_profile_data(self, encrypted_data: bytes) -> dict:
        """Decrypt only for authorized access"""
        decrypted = self.cipher.decrypt(encrypted_data)
        return json.loads(decrypted)
```

### 3. Encryption in Transit

```yaml
# docker-compose.yml
services:
  bejoby_api:
    environment:
      - HTTPS_ONLY=true
      - TLS_MIN_VERSION=1.3
      - HSTS_MAX_AGE=31536000
```

### 4. ARCO Rights Implementation

```python
# api/arco_rights.py
class ARCORights:
    def handle_access_request(self, candidate_email: str):
        """Derecho de ACCESO"""
        # 1. Verify identity
        # 2. Fetch all data on candidate
        # 3. Encrypt export
        # 4. Send via secure channel
        # 5. Log request + response
        pass
    
    def handle_rectification_request(self, candidate_email: str, corrections: dict):
        """Derecho de RECTIFICACIÓN"""
        # 1. Verify identity
        # 2. Update records
        # 3. Log change + timestamp
        # 4. Notify candidate
        # 5. Audit trail
        pass
    
    def handle_deletion_request(self, candidate_email: str):
        """Derecho de CANCELACIÓN"""
        # 1. Verify identity
        # 2. Hard delete (not soft delete)
        # 3. Verify deletion complete
        # 4. Log deletion timestamp
        # 5. Notify candidate + DPO
        pass
    
    def handle_opposition_request(self, candidate_email: str):
        """Derecho de OPOSICIÓN"""
        # 1. Stop marketing emails
        # 2. Don't use for job matching unless explicit re-consent
        # 3. Log opposition
        # 4. Notify candidate
        pass
```

### 5. Audit Logging (MANDATORY)

```python
# utils/audit_log.py
class AuditLogger:
    def log_access(self, user_id: str, candidate_id: str, action: str, reason: str):
        """Every CV access MUST be logged"""
        log = {
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'candidate_id': candidate_id,
            'action': action,  # 'view', 'download', 'process', 'share'
            'reason': reason,  # 'job_matching', 'interview', 'offer'
            'ip_address': request.remote_addr,
            'success': True/False,
        }
        
        # Store in immutable audit table
        audit_table.append(log)
        
        # Alert if unauthorized access
        if not self.is_authorized(user_id, candidate_id):
            alert_dpo(f"Unauthorized CV access: {user_id} → {candidate_id}")
```

### 6. Data Retention Policy

```python
# jobs/retention_cleanup.py
from datetime import datetime, timedelta

def cleanup_expired_consents():
    """Auto-delete data after consent expires"""
    cutoff = datetime.utcnow() - timedelta(days=730)
    
    # Find expired records
    expired = db.query(
        "SELECT * FROM consents WHERE expires_at < ?",
        [cutoff]
    )
    
    for record in expired:
        # Securely delete (not just soft delete)
        db.delete_cascade(record.candidate_id)
        
        # Log deletion
        audit_log.insert({
            'action': 'auto_deletion',
            'candidate_id': record.candidate_id,
            'reason': 'consent_expired',
            'timestamp': datetime.utcnow(),
        })
```

---

## DATABASE SCHEMA (Bejoby - SEPARATE from AIF369)

```sql
-- Bejoby DB (encrypted, separate credentials)

-- Consent records (MUST KEEP for proof)
CREATE TABLE consent_records (
    consent_id UUID PRIMARY KEY,
    candidate_email VARCHAR ENCRYPTED,
    timestamp TIMESTAMP,
    version VARCHAR,
    cv_processing_consent BOOLEAN,
    skill_matching_consent BOOLEAN,
    expires_at TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    CONSTRAINT consent_not_null CHECK (cv_processing_consent IS NOT NULL)
);

-- Candidate profiles (structured from CV)
CREATE TABLE candidate_profiles (
    candidate_id UUID PRIMARY KEY,
    email VARCHAR ENCRYPTED UNIQUE,
    full_name VARCHAR ENCRYPTED,
    phone VARCHAR ENCRYPTED,
    work_experience JSONB ENCRYPTED,
    education JSONB ENCRYPTED,
    skills ARRAY ENCRYPTED,
    location VARCHAR,
    consent_id UUID REFERENCES consent_records,
    profile_score NUMERIC,
    parsed_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    deleted_at TIMESTAMP  -- Soft delete (for compliance)
);

-- Audit logs (IMMUTABLE)
CREATE TABLE audit_logs (
    log_id UUID PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    user_id VARCHAR,
    candidate_id UUID,
    action VARCHAR,  -- 'view', 'download', 'match', 'share'
    reason VARCHAR,
    ip_address INET,
    success BOOLEAN,
    CONSTRAINT no_update CHECK (created_at = NOW())
);

-- ARCO Requests
CREATE TABLE arco_requests (
    request_id UUID PRIMARY KEY,
    candidate_email VARCHAR ENCRYPTED,
    request_type VARCHAR,  -- 'acceso', 'rectificacion', 'cancelacion', 'oposicion'
    status VARCHAR,  -- 'pendiente', 'completado', 'denegado'
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    response_data BYTEA,  -- Encrypted export
    dpo_reviewed BOOLEAN
);
```

---

## BEJOBY RECRUITMENT AGENT (Privacy-First)

```python
# agents/bejoby_recruitment_agent.py
from langgraph.graph import StateGraph
from rag.embeddings import encode_profile
import chromadb

class BejobyRecuitmentAgent:
    """
    IMPORTANT: Only operates on minimized, consented data
    All candidates MUST have explicit consent before processing
    """
    
    def __init__(self, db_connection, audit_logger, llm_client):
        self.db = db_connection
        self.audit = audit_logger
        self.llm = llm_client
        self.chroma = chromadb.Client()
    
    async def process_cv(self, candidate_email: str, cv_file, user_id: str):
        """
        1. Verify consent exists
        2. Extract minimal fields
        3. Encrypt and store
        4. Index for job matching
        5. Log everything
        """
        # STEP 1: Verify consent
        consent = self.db.query(
            "SELECT * FROM consent_records WHERE candidate_email = ?",
            [candidate_email]
        )
        if not consent or consent['expires_at'] < datetime.utcnow():
            self.audit.log_access(user_id, candidate_email, 'rejected', 'no_consent')
            raise PermissionError("No valid consent")
        
        # STEP 2: Extract (data minimization)
        profile_data = self.extract_profile(cv_file)
        minimal_data = {
            'name': profile_data.get('name'),
            'skills': profile_data.get('skills', []),
            'experience_years': profile_data.get('experience_years', 0),
            'location': profile_data.get('location'),
        }
        
        # STEP 3: Encrypt + Store
        candidate_id = uuid.uuid4()
        encrypted_profile = self.encrypt(minimal_data)
        
        self.db.insert('candidate_profiles', {
            'candidate_id': candidate_id,
            'email': candidate_email,
            'consent_id': consent['consent_id'],
            'profile_data': encrypted_profile,
        })
        
        # STEP 4: Index for RAG
        embedding = encode_profile(minimal_data)
        self.chroma.add(
            ids=[str(candidate_id)],
            embeddings=[embedding],
            documents=[json.dumps(minimal_data)]
        )
        
        # STEP 5: Log
        self.audit.log_access(
            user_id, 
            candidate_id, 
            'cv_processed',
            'job_matching'
        )
        
        return candidate_id
    
    async def find_matching_jobs(self, candidate_id: str) -> list:
        """Find jobs matching candidate skills"""
        # Decrypt profile data
        profile = self.decrypt(candidate_id)
        
        # Find matching jobs
        matching_jobs = self.search_jobs(profile['skills'])
        
        # Log search
        self.audit.log_access(
            'system',
            candidate_id,
            'skill_match_query',
            'job_recommendation'
        )
        
        return matching_jobs
```

---

## INTEGRATION WITH AIF369 CONVERSATIONAL AGENTS

```
AIF369.com (Visitor-facing)
    ├─ Profile 360 Agent (AIF369 clients data)
    │   └─ LangGraph conversational
    │
    └─ Bejoby Link (SEPARATE domain)
        ├─ Consent gateway
        ├─ CV upload (encrypted)
        ├─ Recruitment Agent (privacy-compliant)
        └─ ARCO rights portal

⚠️ CRITICAL: No CV data flows into AIF369 core
⚠️ CRITICAL: Bejoby has separate DB, encryption keys, audit logs
⚠️ CRITICAL: ARCO requests handled separately from sales queries
```

---

## COMPLIANCE CHECKLIST BEFORE LAUNCH

```
Legal/Compliance:
□ Privacy Policy (Ley 21.719 compliant) on bejoby.com
□ Terms of Service with data processing disclosure
□ DPO (Data Protection Officer) designated
□ Data Processing Agreement with Zoho Mail

Technical:
□ Encryption at rest (AES-256)
□ Encryption in transit (TLS 1.3)
□ Audit logging (immutable)
□ ARCO endpoints implemented
□ Data retention policy automated
□ Access control (role-based)
□ Consent form on CV upload page

Operational:
□ DPO review process for ARCO requests
□ Breach notification protocol
□ Training for staff accessing CVs
□ Regular security audits
□ Incident response plan

Testing:
□ Test ARCO access request
□ Test ARCO deletion request
□ Test consent expiration cleanup
□ Test unauthorized access logging
□ Test encryption/decryption
```

---

## TIMELINE TO COMPLIANCE

```
PHASE 0 (Week 1): Consent + Privacy Policy
- Launch consent form on CV upload
- Publish privacy policy
- Designate DPO (you or external)

PHASE 1 (Week 2): Encryption
- Implement AES-256 encryption
- Migrate existing CVs (if consent obtained)
- Set up key rotation

PHASE 2 (Week 3): ARCO Rights
- Build ARCO request endpoints
- Test access/deletion workflows
- Set up DPO approval process

PHASE 3 (Week 4): Audit + Retention
- Complete audit logging
- Implement auto-deletion after 2 years
- Final security audit

Ready for Ley 21.719 compliance: Week 4
```

---

## COST STRUCTURE (Bejoby Recruitment)

```
Bejoby DB (PostgreSQL encrypted): $15/month
Zoho Mail (current): $0 (part of AIF369)
Encryption keys (AWS KMS): $1/month
Audit logging: $2/month
─────────────────────────────
TOTAL: ~$18/month (can be absorbed into AIF369 budget)
```

---

## ⚠️ CRITICAL NOTES

1. **Bejoby ≠ AIF369 Data**: Keep completely separate
2. **Consent is MANDATORY**: No CV processing without explicit consent
3. **2-Year Retention**: Auto-delete after expiration
4. **ARCO Rights are LAW**: Not optional, implement before Dec 1
5. **DPO Oversight**: Designate someone to review ARCO requests
6. **Audit Immutable**: Logs cannot be deleted (evidence for compliance)

---

**Ready to implement Phase 0 + Bejoby compliance?**
