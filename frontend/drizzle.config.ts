// import { config } from 'dotenv';
// import { defineConfig } from 'drizzle-kit';

// config({
//   path: '.env.local',
// });

// export default defineConfig({
//   schema: './lib/db/schema.ts',
//   out: './lib/db/migrations',
//   dialect: 'postgresql',
//   dbCredentials: {
//     // biome-ignore lint: Forbidden non-null assertion.
//     url: process.env.POSTGRES_URL!,
//   },
// });

import { pgTable, serial, varchar, text, date, time, jsonb } from 'drizzle-orm/pg-core';
import { config } from 'dotenv';
import { defineConfig } from 'drizzle-kit';
import { resolve } from 'path';

config({
  path: resolve('.env.local'),
});

// Add definitions for existing tables
export const events = pgTable('events', {
  event_id: serial('event_id').primaryKey(),
  event_name: varchar('event_name', { length: 255 }).notNull(),
  event_description: text('event_description'),
  event_location: varchar('event_location', { length: 255 }),
  date: date('date').notNull(),
  start_time: time('start_time').notNull(),
  end_time: time('end_time').notNull(),
});

export const timeslots = pgTable('timeslots', {
  slot_id: serial('slot_id').primaryKey(),
  event_id: jsonb('event_id'),
  date: date('date').notNull(),
  start_time: time('start_time').notNull(),
  end_time: time('end_time').notNull(),
});

export default defineConfig({
  schema: './lib/db/schema.ts',
  out: './lib/db/migrations',
  dialect: 'postgresql',
  dbCredentials: {
    host: process.env.POSTGRES_HOST!,
    port: parseInt(process.env.POSTGRES_PORT!, 10),
    user: process.env.POSTGRES_USER!,
    password: process.env.POSTGRES_PASSWORD!,
    database: process.env.POSTGRES_DB!,
    ssl: 'require'
  },
});