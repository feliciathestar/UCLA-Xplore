'use client';

import { useState } from 'react';
import TimeTable from './timetable';

interface TimeSlot {
  date: string;
  start_time: string;
  end_time: string;
}

export default function TimeTableSidebar() {
  const [currentTimeSlots, setCurrentTimeSlots] = useState<TimeSlot[]>([]);
  const [selectedBoxes, setSelectedBoxes] = useState<number[]>([]);
  const [showDebug, setShowDebug] = useState(true);

  const handleTimeSlotChange = (timeSlots: TimeSlot[]) => {
    setCurrentTimeSlots(timeSlots);
    console.log("🔄 Time slots updated for PostgreSQL query:");
    console.log("📅 Time slots data:", timeSlots);
    console.log("🚀 Would call: query_postgres(null, timeSlots)");
    
    // Pretty print the data that would be sent to backend
    if (timeSlots.length > 0) {
      console.log("📋 Backend payload preview:");
      timeSlots.forEach((slot, index) => {
        console.log(`   ${index + 1}. ${slot.date} from ${slot.start_time} to ${slot.end_time}`);
      });
    }
  };

  const handleSelectionChange = (selection: number[]) => {
    setSelectedBoxes(selection);
    console.log("📦 Selected boxes:", selection);
  };

  return (
    <div className="h-full flex flex-col">
      {/* Debug toggle */}
      <div className="mb-2 flex justify-between items-center">
        <h3 className="text-sm font-medium">Time Selection</h3>
        <button
          onClick={() => setShowDebug(!showDebug)}
          className="text-xs px-2 py-1 bg-blue-100 hover:bg-blue-200 rounded text-blue-700"
        >
          {showDebug ? 'Hide' : 'Show'} Debug
        </button>
      </div>

      {/* TimeTable component */}
      <div className="flex-1 min-h-0">
        <TimeTable 
          rows={15} 
          cols={7}
          onTimeSlotChange={handleTimeSlotChange}
          onSelectionChange={handleSelectionChange}
        />
      </div>

      {/* Debug Panel */}
      {showDebug && (
        <div className="mt-4 space-y-3">
          {/* Selection Summary */}
          <div className="text-xs">
            <div className="font-medium text-gray-700 mb-1">
              Selected: {selectedBoxes.length} boxes
            </div>
            <div className="font-medium text-gray-700 mb-1">
              Time slots: {currentTimeSlots.length}
            </div>
          </div>

          {/* PostgreSQL Query Preview */}
          <div className="border rounded p-2 bg-gray-50 max-h-32 overflow-y-auto">
            <div className="text-xs font-medium text-gray-700 mb-1">
              PostgreSQL Query Data:
            </div>
            <pre className="text-xs text-gray-600 whitespace-pre-wrap">
              {currentTimeSlots.length > 0 
                ? JSON.stringify(currentTimeSlots, null, 2)
                : "No time slots selected"
              }
            </pre>
          </div>

          {/* Quick Action */}
          <button
            onClick={() => {
              console.clear();
              console.log("🧪 TEST: Current time slots for backend:");
              console.log(currentTimeSlots);
            }}
            className="w-full text-xs py-1 px-2 bg-green-100 hover:bg-green-200 rounded text-green-700"
          >
            Log to Console
          </button>
        </div>
      )}
    </div>
  );
}