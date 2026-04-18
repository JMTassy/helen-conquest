// web-frontend/src/services/verifiableCredentials.ts
/**
 * ORACLE SUPERTEAM — Verifiable Credentials Service
 *
 * Generates W3C Verifiable Credentials for satisfied obligations.
 * Provides cryptographic proof of obligation completion.
 */

import { VerifiableCredential, Obligation, ObligationType, Evidence } from '../types/oracle';

export class VerifiableCredentialsService {
  private issuerDID: string = 'did:oracle:issuer:main';

  /**
   * Generate a Verifiable Credential for a satisfied obligation
   */
  public async generateCredential(
    obligation: Obligation,
    claimId: string,
    evidence: Evidence[]
  ): Promise<VerifiableCredential> {
    const now = new Date().toISOString();

    // Create credential subject
    const credentialSubject = {
      id: `did:oracle:obligation:${this.generateId()}`,
      obligationType: obligation.type,
      claimId,
      satisfactionProof: this.generateSatisfactionProof(obligation, evidence),
      evidence: evidence.map(e => ({
        type: e.type,
        hash: e.hash || this.hashContent(e.content || ''),
        timestamp: now
      }))
    };

    // Create proof (simplified JWS-like format)
    const proof = await this.generateProof(credentialSubject, now);

    const credential: VerifiableCredential = {
      '@context': [
        'https://www.w3.org/2018/credentials/v1',
        'https://oracle-superteam.io/contexts/v1'
      ],
      type: ['VerifiableCredential', 'OracleObligationCredential'],
      issuer: this.issuerDID,
      issuanceDate: now,
      credentialSubject,
      proof
    };

    return credential;
  }

  /**
   * Verify a Verifiable Credential
   */
  public async verifyCredential(credential: VerifiableCredential): Promise<boolean> {
    try {
      // 1. Check structure
      if (!credential['@context'] || !credential.type || !credential.proof) {
        return false;
      }

      // 2. Verify issuer
      if (credential.issuer !== this.issuerDID) {
        console.warn('Unknown issuer:', credential.issuer);
        return false;
      }

      // 3. Verify proof signature
      const isValidSignature = await this.verifyProof(
        credential.credentialSubject,
        credential.proof
      );

      if (!isValidSignature) {
        return false;
      }

      // 4. Check evidence hashes
      for (const evidence of credential.credentialSubject.evidence) {
        if (!evidence.hash || evidence.hash.length === 0) {
          return false;
        }
      }

      // 5. Verify satisfaction proof
      const isValidSatisfaction = this.verifySatisfactionProof(
        credential.credentialSubject.satisfactionProof,
        credential.credentialSubject.obligationType
      );

      return isValidSatisfaction;
    } catch (error) {
      console.error('Credential verification failed:', error);
      return false;
    }
  }

  /**
   * Generate satisfaction proof for an obligation
   */
  private generateSatisfactionProof(obligation: Obligation, evidence: Evidence[]): string {
    // Combine obligation details and evidence into a proof string
    const proofData = {
      obligation_type: obligation.type,
      owner_team: obligation.owner_team,
      closure_criteria: obligation.closure_criteria,
      evidence_hashes: evidence.map(e => e.hash || this.hashContent(e.content || '')),
      timestamp: new Date().toISOString()
    };

    // Generate deterministic hash
    return this.hashContent(JSON.stringify(proofData, Object.keys(proofData).sort()));
  }

  /**
   * Verify satisfaction proof
   */
  private verifySatisfactionProof(proof: string, obligationType: ObligationType): boolean {
    // Basic validation: proof should be a valid hash format
    return /^[a-f0-9]{64}$/i.test(proof);
  }

  /**
   * Generate cryptographic proof (simplified)
   */
  private async generateProof(
    subject: any,
    timestamp: string
  ): Promise<VerifiableCredential['proof']> {
    // In production, use proper cryptographic signing (Ed25519, ECDSA, etc.)
    // This is a simplified version for demonstration

    const payload = JSON.stringify(subject, Object.keys(subject).sort());
    const signature = await this.signData(payload);

    return {
      type: 'Ed25519Signature2020',
      created: timestamp,
      proofPurpose: 'assertionMethod',
      verificationMethod: `${this.issuerDID}#keys-1`,
      jws: signature
    };
  }

  /**
   * Verify cryptographic proof
   */
  private async verifyProof(
    subject: any,
    proof: VerifiableCredential['proof']
  ): Promise<boolean> {
    try {
      const payload = JSON.stringify(subject, Object.keys(subject).sort());
      return await this.verifySignature(payload, proof.jws);
    } catch (error) {
      console.error('Proof verification failed:', error);
      return false;
    }
  }

  /**
   * Sign data (simplified - use Web Crypto API in production)
   */
  private async signData(data: string): Promise<string> {
    // In production, use SubtleCrypto.sign() with a private key
    // For now, generate deterministic hash-based signature
    const hash = await this.hashContent(data + this.issuerDID);
    return `eyJhbGciOiJFZDI1NTE5IiwidHlwIjoiSldUIn0.${hash}`;
  }

  /**
   * Verify signature
   */
  private async verifySignature(data: string, signature: string): Promise<boolean> {
    // In production, use SubtleCrypto.verify()
    // For now, just check format
    return signature.startsWith('eyJhbGciOiJFZDI1NTE5');
  }

  /**
   * Hash content using SHA-256
   */
  private async hashContent(content: string): Promise<string> {
    if (typeof window !== 'undefined' && window.crypto && window.crypto.subtle) {
      // Browser environment with Web Crypto API
      const encoder = new TextEncoder();
      const data = encoder.encode(content);
      const hashBuffer = await window.crypto.subtle.digest('SHA-256', data);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    } else {
      // Fallback: simple hash function (NOT cryptographically secure)
      let hash = 0;
      for (let i = 0; i < content.length; i++) {
        const char = content.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
      }
      return Math.abs(hash).toString(16).padStart(64, '0');
    }
  }

  /**
   * Generate unique ID
   */
  private generateId(): string {
    return Date.now().toString(36) + Math.random().toString(36).substr(2);
  }

  /**
   * Export credential as JSON
   */
  public exportCredential(credential: VerifiableCredential): string {
    return JSON.stringify(credential, null, 2);
  }

  /**
   * Import credential from JSON
   */
  public importCredential(json: string): VerifiableCredential {
    return JSON.parse(json) as VerifiableCredential;
  }

  /**
   * Generate QR code data for credential (for mobile verification)
   */
  public generateQRData(credential: VerifiableCredential): string {
    // Encode credential as base64 for QR code
    const json = JSON.stringify(credential);
    if (typeof window !== 'undefined' && window.btoa) {
      return window.btoa(json);
    }
    return Buffer.from(json).toString('base64');
  }

  /**
   * Create a Verifiable Presentation containing multiple credentials
   */
  public createPresentation(credentials: VerifiableCredential[]): any {
    return {
      '@context': [
        'https://www.w3.org/2018/credentials/v1'
      ],
      type: 'VerifiablePresentation',
      verifiableCredential: credentials,
      holder: this.issuerDID,
      created: new Date().toISOString()
    };
  }
}

// Singleton instance
export const vcService = new VerifiableCredentialsService();
