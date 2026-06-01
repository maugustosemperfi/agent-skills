# PRD: User Authentication System

## Overview
Add a complete user authentication system to the application, including registration, login, password reset, and session management.

## Requirements

### R1: User Registration
- Users can register with email and password
- Password must be at least 8 characters with at least one uppercase letter and one number
- Email must be validated for format and uniqueness
- On successful registration, send a welcome email
- Store passwords hashed using bcrypt with a salt round of 12

### R2: User Login
- Users can log in with email and password
- On successful login, create a JWT session token valid for 24 hours
- On failed login, return a generic error (don't reveal whether email exists)
- After 5 failed attempts from the same IP, lock the account for 15 minutes

### R3: Password Reset
- Users can request a password reset via email
- Reset tokens expire after 1 hour
- New password must meet the same requirements as registration
- After reset, invalidate all existing sessions

### R4: Session Management
- JWT tokens stored in httpOnly cookies
- Middleware to verify tokens on protected routes
- Token refresh endpoint that extends session without re-login
- Logout endpoint that invalidates the current token

### R5: Tests
- Unit tests for password validation logic
- Unit tests for token generation and verification
- Integration tests for registration and login flows
- All tests must pass before merging

## Non-functional Requirements
- All endpoints must use HTTPS
- Rate limiting on auth endpoints (max 10 requests per minute per IP)
- Log all authentication events for audit purposes
