import { compare } from 'bcrypt-ts';
import NextAuth, { type User, type Session } from 'next-auth';
import Credentials from 'next-auth/providers/credentials';

import { getUser } from '@/lib/db/queries';
import jwt from 'jsonwebtoken';

import { authConfig } from './auth.config';

interface ExtendedSession extends Session {
  user: User;
  token?: string; // Add the token property
}

export const {
  handlers: { GET, POST },
  auth,
  signIn,
  signOut,
} = NextAuth({
  ...authConfig,
  secret: process.env.AUTH_SECRET,
  providers: [
    Credentials({
      credentials: {},
      async authorize({ email, password }: any) {
        try {
          console.log('Attempting to authorize user:', email);
          
          // Get user from database
          const users = await getUser(email);
          console.log('Database query completed', { userFound: users.length > 0 });
          
          if (users.length === 0) {
            console.log('No user found with email:', email);
            return null;
          }

          // Check password
          console.log('Verifying password...');
          const passwordsMatch = await compare(password, users[0].password ?? '');
          console.log('Password verification completed:', { isMatch: passwordsMatch });

          if (!passwordsMatch) {
            console.log('Password mismatch for user:', email);
            return null;
          }

          // Generate JWT token
          console.log('Generating JWT token...');
          const access_token = jwt.sign(
            { sub: users[0].id, email: users[0].email },
            process.env.AUTH_SECRET!,
            { expiresIn: '1h' }
          );

          console.log('Authorization successful for user:', email);
          return {
            id: users[0].id,
            email: users[0].email,
            access_token: access_token,
            // Don't include password in the return object
          } as User;

        } catch (error) {
          console.error('Authorization error:', {
            step: 'authorize',
            error: error instanceof Error ? error.message : 'Unknown error',
            email,
            timestamp: new Date().toISOString()
          });
          return null;
        }
      },
    }),
  ],

  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
      }

      return token;
    },
    async session({
      session,
      token,
    }: {
      session: ExtendedSession;
      token: any;
    }) {
      if (session.user) {
        session.user.id = token.id as string;
        session.token = token.access_token;
      }

      return session;
    },
  },
});
