# Test Plan - ft-lineone

## Unit Tests (Vitest Workers)

### Auth Service Tests
- ✅ Token creation (access + refresh)
- ✅ Token verification (valid, wrong type, wrong secret, malformed, wrong algorithm)
- ✅ Password hashing (hash + verify, wrong password, unique salts)
- ✅ Base64URL encoding/decoding

### LLM Service Tests (pending)
- [ ] Recommendations with RAG
- [ ] Style advice with model router
- [ ] VTON flow with Moondream pre-check
- [ ] Streaming responses

### VTON Service Tests (pending)
- [ ] Image upload to R2
- [ ] YouCam polling
- [ ] Result persistence
- [ ] Refund on failure

### Auth Service Tests (pending)
- [ ] Turnstile verification
- [ ] EdDSA JWT signing/verification
- [ ] Rate limiting

---

## Integration Tests (Vitest)

- [ ] API endpoint testing with mocked bindings
- [ ] Database operations
- [ ] R2 operations

---

## E2E Tests (Playwright)

### Critical Paths
- ✅ Home page loads
- ✅ Navigation (Catalog, VTON, Chat, Profile)
- ✅ Login/Register flows
- ✅ VTON upload → process → result
- ✅ Chatbot streaming responses
- ✅ Payment flow (Transbank redirect)
- ✅ Mobile responsiveness

### Critical User Journeys
1. **New User**: Register → VTON → Try 3 items → Upgrade to Premium
2. **Returning User**: Login → Chat with AI → Try on 2 items → Save to favorites
3. **Premium User**: Login → Unlimited VTON → Chat with DeepSeek R1 reasoning

---

## Test Commands

```bash
# Unit tests
cd workers && npm run test

# Integration tests
cd workers && npm run test:integration

# E2E tests
cd frontend-astro && npm run test:e2e

# All tests
npm run test:all
```

---

## Coverage Targets

| Layer | Target |
|-------|--------|
| Unit | ≥80% |
| Integration | ≥60% |
| E2E Critical Paths | 100% |