import React, { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import { Alert, AlertDescription } from './components/ui/alert';
import { Button } from './components/ui/button';

const TimeSlotSelector = () => {
  const [isMouseDown, setIsMouseDown] = useState(false);
  const [selectedSlots, setSelectedSlots] = useState({});
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  
  // Generate time slots from 9 AM to 5 PM
  const times = Array.from({ length: 17 }, (_, i) => {
    const hour = Math.floor(i / 2) + 9;
    const minute = i % 2 === 0 ? '00' : '30';
    return `${hour}:${minute}`;
  });

  // Generate dates for the next 5 days
  const dates = Array.from({ length: 5 }, (_, i) => {
    const date = new Date();
    date.setDate(date.getDate() + i);
    return {
      display: date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' }),
      iso: date.toISOString().split('T')[0]
    };
  });

  // Load existing selections when component mounts
  useEffect(() => {
    loadExistingSelections();
  }, []);

  const loadExistingSelections = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Replace with your API endpoint
      const response = await fetch('/api/availability');
      if (!response.ok) throw new Error('Failed to load availability');
      
      const data = await response.json();
      
      // Convert API data to component state format
      const formattedSelections = {};
      data.forEach(slot => {
        const timeIndex = times.findIndex(time => time === slot.time);
        const dateIndex = dates.findIndex(date => date.iso === slot.date);
        if (timeIndex !== -1 && dateIndex !== -1) {
          formattedSelections[`${timeIndex}-${dateIndex}`] = true;
        }
      });
      
      setSelectedSlots(formattedSelections);
    } catch (err) {
      setError('Failed to load existing selections. Please try again.');
      console.error('Load error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Save a single time slot selection
  const saveTimeSlot = async (timeIndex, dateIndex, isSelected) => {
    try {
      setError(null);
      
      // Prepare the data for the API
      const data = {
        date: dates[dateIndex].iso,
        time: times[timeIndex],
        isAvailable: isSelected
      };
      
      // Replace with your API endpoint
      const response = await fetch('/api/availability', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });
      
      if (!response.ok) throw new Error('Failed to save selection');
      
    } catch (err) {
      setError('Failed to save selection. Please try again.');
      console.error('Save error:', err);
    }
  };

  // Bulk save all selections
  const saveAllSelections = async () => {
    try {
      setIsSaving(true);
      setError(null);
      
      // Convert selected slots to API format
      const selections = Object.entries(selectedSlots).map(([key, isSelected]) => {
        const [timeIndex, dateIndex] = key.split('-').map(Number);
        return {
          date: dates[dateIndex].iso,
          time: times[timeIndex],
          isAvailable: isSelected
        };
      });
      
      // Replace with your API endpoint
      const response = await fetch('/api/availability/bulk', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ selections })
      });
      
      if (!response.ok) throw new Error('Failed to save selections');
      
      setHasUnsavedChanges(false);
    } catch (err) {
      setError('Failed to save selections. Please try again.');
      console.error('Bulk save error:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleMouseDown = (timeIndex, dateIndex) => {
    setIsMouseDown(true);
    toggleTimeSlot(timeIndex, dateIndex);
  };

  const handleMouseEnter = (timeIndex, dateIndex) => {
    if (isMouseDown) {
      toggleTimeSlot(timeIndex, dateIndex);
    }
  };

  const handleMouseUp = () => {
    setIsMouseDown(false);
  };

  const toggleTimeSlot = (timeIndex, dateIndex) => {
    const key = `${timeIndex}-${dateIndex}`;
    const newValue = !selectedSlots[key];
    
    setSelectedSlots(prev => ({
      ...prev,
      [key]: newValue
    }));
    
    setHasUnsavedChanges(true);
    
    // Optionally, save individual selections immediately
    // saveTimeSlot(timeIndex, dateIndex, newValue);
  };

  useEffect(() => {
    window.addEventListener('mouseup', handleMouseUp);
    return () => window.removeEventListener('mouseup', handleMouseUp);
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading availability...</span>
      </div>
    );
  }

  return (
    <div className="p-4 max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-4">
        <div className="text-lg font-bold">Time Slot Selector</div>
        {hasUnsavedChanges && (
          <Button 
            onClick={saveAllSelections}
            disabled={isSaving}
            className="flex items-center gap-2"
          >
            {isSaving && <Loader2 className="h-4 w-4 animate-spin" />}
            Save Changes
          </Button>
        )}
      </div>
      
      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      
      <div className="grid grid-flow-col auto-cols-fr border border-gray-200">
        <div className="border-r border-gray-200">
          <div className="h-10 border-b border-gray-200"></div>
          {times.map((time, i) => (
            <div key={i} className="h-8 border-b border-gray-200 text-sm px-2 py-1">
              {time}
            </div>
          ))}
        </div>
        
        {dates.map((date, dateIndex) => (
          <div key={dateIndex} className="border-r border-gray-200">
            <div className="h-10 border-b border-gray-200 text-sm font-medium p-2">
              {date.display}
            </div>
            {times.map((_, timeIndex) => (
              <div
                key={timeIndex}
                className={`h-8 border-b border-gray-200 cursor-pointer ${
                  selectedSlots[`${timeIndex}-${dateIndex}`] ? 'bg-blue-500' : 'hover:bg-gray-100'
                }`}
                onMouseDown={() => handleMouseDown(timeIndex, dateIndex)}
                onMouseEnter={() => handleMouseEnter(timeIndex, dateIndex)}
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

export default TimeSlotSelector;
