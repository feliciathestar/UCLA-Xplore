import { pgTable, serial, varchar, text, date, time, jsonb } from "drizzle-orm/pg-core"
  import { sql } from "drizzle-orm"




export const events = pgTable("events", {
	eventId: serial("event_id").primaryKey().notNull(),
	eventName: varchar("event_name", { length: 255 }).notNull(),
	eventDescription: text("event_description"),
	eventLocation: varchar("event_location", { length: 255 }),
	date: date().notNull(),
	startTime: time("start_time").notNull(),
	endTime: time("end_time").notNull(),
});

export const timeslots = pgTable("timeslots", {
	slotId: serial("slot_id").primaryKey().notNull(),
	eventId: jsonb("event_id"),
	date: date().notNull(),
	startTime: time("start_time").notNull(),
	endTime: time("end_time").notNull(),
});