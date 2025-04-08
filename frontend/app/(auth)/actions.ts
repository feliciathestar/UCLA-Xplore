'use server';

import { z } from 'zod';

import { createUser, getUser } from '@/lib/db/queries';

import { signIn } from './auth';

const authFormSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
});

export interface LoginActionState {
  status: 'idle' | 'in_progress' | 'success' | 'failed' | 'invalid_data';
}

export const login = async (
  _: LoginActionState,
  formData: FormData,
): Promise<LoginActionState> => {
  try {
    const validatedData = authFormSchema.parse({
      email: formData.get('email'),
      password: formData.get('password'),
    });

    await signIn('credentials', {
      email: validatedData.email,
      password: validatedData.password,
      redirect: false,
    });

    return { status: 'success' };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return { status: 'invalid_data' };
    }

    return { status: 'failed' };
  }
};

export interface RegisterActionState {
  status:
    | 'idle'
    | 'in_progress'
    | 'success'
    | 'failed'
    | 'user_exists'
    | 'invalid_data';
}

export const register = async (
  _: RegisterActionState,
  formData: FormData,
): Promise<RegisterActionState> => {
  // try {
  //   const validatedData = authFormSchema.parse({
  //     email: formData.get('email'),
  //     password: formData.get('password'),
  //   });

  //   const [user] = await getUser(validatedData.email);

  //   if (user) {
  //     return { status: 'user_exists' } as RegisterActionState;
  //   }
  //   await createUser(validatedData.email, validatedData.password);
  //   await signIn('credentials', {
  //     email: validatedData.email,
  //     password: validatedData.password,
  //     redirect: false,
  //   });

  //   return { status: 'success' };
  // } 
  try {
    console.log('Starting registration process for email:', formData.get('email'));
    
    // Log validation attempt
    console.log('Validating form data...');
    const validatedData = authFormSchema.parse({
      email: formData.get('email'),
      password: formData.get('password'),
    });
    console.log('Form data validation successful');

    // Log user check
    console.log('Checking if user exists...');
    const [user] = await getUser(validatedData.email);
    if (user) {
      console.log('User already exists with email:', validatedData.email);
      return { status: 'user_exists' } as RegisterActionState;
    }
    console.log('User does not exist, proceeding with creation');

    // Log user creation attempt
    console.log('Attempting to create new user...');
    await createUser(validatedData.email, validatedData.password);
    console.log('User created successfully');

    // Log sign-in attempt
    console.log('Attempting to sign in user...');
    await signIn('credentials', {
      email: validatedData.email,
      password: validatedData.password,
      redirect: false,
    });
    console.log('Sign in successful');

    return { status: 'success' };
    } 
    catch (error) {
    if (error instanceof z.ZodError) {
      return { status: 'invalid_data' };
    }

    return { status: 'failed' };
  }
};
