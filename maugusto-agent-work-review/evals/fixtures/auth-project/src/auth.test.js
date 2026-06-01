const { validatePassword } = require('../src/auth');

describe('Password Validation', () => {
  test('rejects passwords shorter than 8 characters', () => {
    expect(validatePassword('abc')).toBe(false);
  });

  test('accepts valid password', () => {
    expect(validatePassword('MyPassword1')).toBe(true);
  });

  // TODO: add tests for uppercase requirement
  // TODO: add tests for number requirement
});
