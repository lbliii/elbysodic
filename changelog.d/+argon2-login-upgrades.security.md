New real accounts now use argon2id password hashes, while successful logins atomically upgrade legacy PBKDF2 or scrypt hashes without rewriting failed, current, or demo-seed credentials.
