'use client';

import { useState, useCallback } from 'react';
import TimeTable from './timetable';

interface TimeSlot {
  date: string;
  start_time: string;
  end_time: string;
}

export default function TimeTableWithTesting() {
  const [currentTimeSlots, setCurrentTimeSlots] = useState<TimeSlot[]>([]);

  // Memoize the callback to prevent infinite re-renders
  const handleTimeSlotChange = useCallback((timeSlots: TimeSlot[]) => {
    setCurrentTimeSlots(timeSlots);
    console.log("🔄 Time slots updated for PostgreSQL query:");
    console.log("📅 Time slots data:", timeSlots);
    console.log("🚀 Would call: query_postgres(null, timeSlots)");
  }, []);

  // Memoize this callback too
  const handleSelectionChange = useCallback((selection: number[]) => {
    console.log("📦 Selected boxes:", selection);
  }, []);

  return (
    <div className="h-full flex flex-col">
      <TimeTable 
        rows={15} 
        cols={7}
        onTimeSlotChange={handleTimeSlotChange}
        onSelectionChange={handleSelectionChange}
      />
      
      {/* Simple debug display */}
      <div className="mt-2 p-2 bg-gray-50 rounded text-xs max-h-24 overflow-y-auto">
        <div className="font-medium mb-1">PostgreSQL Data:</div>
        <pre className="text-xs">
          {currentTimeSlots.length > 0 
            ? JSON.stringify(currentTimeSlots, null, 2)
            : "No selections"
          }
        </pre>
      </div>
    </div>
  );
}