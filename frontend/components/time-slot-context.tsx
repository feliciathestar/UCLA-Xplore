"use client";

import { createContext, useContext, useState } from 'react';

interface TimeSlot {
  date: string;
  start_time: string;
  end_time: string;
}

interface TimeSlotContextType {
  timeSlots: TimeSlot[];
  setTimeSlots: (slots: TimeSlot[]) => void;
  clearTimeSlots: () => void;
  isTimeSlotOpen: boolean;
  toggleTimeSlot: () => void;
}

const TimeSlotContext = createContext<TimeSlotContextType | undefined>(undefined);

export function TimeSlotProvider({ children }: { children: React.ReactNode }) {
  const [timeSlots, setTimeSlots] = useState<TimeSlot[]>([]);
  const [isTimeSlotOpen, setIsTimeSlotOpen] = useState(false);

  const clearTimeSlots = () => setTimeSlots([]);
  const toggleTimeSlot = () => setIsTimeSlotOpen(!isTimeSlotOpen);

  return (
    <TimeSlotContext.Provider
      value={{
        timeSlots,
        setTimeSlots,
        clearTimeSlots,
        isTimeSlotOpen,
        toggleTimeSlot,
      }}
    >
      {children}
    </TimeSlotContext.Provider>
  );
}

export function useTimeSlots() {
  const context = useContext(TimeSlotContext);
  if (!context) {
    throw new Error('useTimeSlots must be used within TimeSlotProvider');
  }
  return context;
}