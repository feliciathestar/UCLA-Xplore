"use client"; 

import React, { useState, useCallback, useEffect, useMemo } from "react";

// Define the default date object outside the component to ensure a stable reference
const DEFAULT_INITIAL_START_DATE = new Date("2025-05-12");

interface TimeSlot {
  date: string;
  start_time: string;
  end_time: string;
}

interface TimeTableProps {
  rows?: number;
  cols?: number;
  initialStartDate?: Date;
  startHour?: number;
  onSelectionChange?: (selection: number[]) => void;
  onTimeSlotChange?: (timeSlots: TimeSlot[]) => void;
}

const TimeTable: React.FC<TimeTableProps> = ({
  rows = 15,
  cols = 7,
  initialStartDate = DEFAULT_INITIAL_START_DATE, // Use the stable default date
  startHour = 8, 
  onSelectionChange,
  onTimeSlotChange,
}) => {
  const actualRows = rows * 2;
  
  const [isMouseDown, setIsMouseDown] = useState(false);
  const [selectedBoxes, setSelectedBoxes] = useState<number[]>([]);
  const [currentSelection, setCurrentSelection] = useState<number[]>([]);
  const [isDeselecting, setIsDeselecting] = useState(false);
  const [startBox, setStartBox] = useState<number | null>(null);

  // Memoize the boxToDateTime function to prevent unnecessary re-renders
  const boxToDateTime = useCallback((boxNumber: number) => {
    const rowIndex = Math.floor((boxNumber - 1) / cols);
    const colIndex = (boxNumber - 1) % cols;
    
    // Create a new date and ensure we're working with the start of day in local time
    const date = new Date(initialStartDate.getFullYear(), initialStartDate.getMonth(), initialStartDate.getDate());
    
    // Find the Monday of the week containing initialStartDate
    if (date.getDay() !== 1) {
      const daysUntilMonday = (1 - date.getDay() + 7) % 7;
      date.setDate(date.getDate() + daysUntilMonday);
    }
    
    // Add the column offset
    date.setDate(date.getDate() + colIndex);
    
    const totalMinutes = startHour * 60 + (rowIndex * 30);
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;
    
    return {
      date: date.toISOString().split('T')[0],
      time: `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:00`
    };
  }, [initialStartDate, cols, startHour]);

  // Memoize the convertToTimeSlots function to prevent unnecessary calculations
  const convertToTimeSlots = useCallback((selectedBoxes: number[]): TimeSlot[] => {
    if (selectedBoxes.length === 0) return [];
    
    const dateGroups: { [date: string]: number[] } = {};
    
    selectedBoxes.forEach(boxNumber => {
      const { date } = boxToDateTime(boxNumber);
      if (!dateGroups[date]) {
        dateGroups[date] = [];
      }
      dateGroups[date].push(boxNumber);
    });
    
    const timeSlots: TimeSlot[] = [];
    
    Object.entries(dateGroups).forEach(([date, boxes]) => {
      boxes.sort((a, b) => {
        const rowA = Math.floor((a - 1) / cols);
        const rowB = Math.floor((b - 1) / cols);
        return rowA - rowB;
      });
      
      let rangeStart = boxes[0];
      let rangeEnd = boxes[0];
      
      for (let i = 1; i < boxes.length; i++) {
        const currentBox = boxes[i];
        const previousBox = boxes[i - 1];
        
        const currentRow = Math.floor((currentBox - 1) / cols);
        const previousRow = Math.floor((previousBox - 1) / cols);
        const currentCol = (currentBox - 1) % cols;
        const previousCol = (previousBox - 1) % cols;
        
        if (currentCol === previousCol && currentRow === previousRow + 1) {
          rangeEnd = currentBox;
        } else {
          const startDateTime = boxToDateTime(rangeStart);
          const endDateTime = boxToDateTime(rangeEnd);
          
          const endTime = new Date(`2000-01-01T${endDateTime.time}`);
          endTime.setMinutes(endTime.getMinutes() + 30);
          const endTimeStr = endTime.toTimeString().split(' ')[0];
          
          timeSlots.push({
            date: startDateTime.date,
            start_time: startDateTime.time,
            end_time: endTimeStr
          });
          
          rangeStart = currentBox;
          rangeEnd = currentBox;
        }
      }
      
      const startDateTime = boxToDateTime(rangeStart);
      const endDateTime = boxToDateTime(rangeEnd);
      
      const endTime = new Date(`2000-01-01T${endDateTime.time}`);
      endTime.setMinutes(endTime.getMinutes() + 30);
      const endTimeStr = endTime.toTimeString().split(' ')[0];
      
      timeSlots.push({
        date: startDateTime.date,
        start_time: startDateTime.time,
        end_time: endTimeStr
      });
    });
    
    return timeSlots;
  }, [boxToDateTime, cols]);

  // Memoize the time slots to prevent unnecessary recalculations
  const timeSlots = useMemo(() => convertToTimeSlots(selectedBoxes), [convertToTimeSlots, selectedBoxes]);

  // Replace the problematic useEffects with these
  useEffect(() => {
    if (onSelectionChange) {
      onSelectionChange(selectedBoxes);
    }
  }, [selectedBoxes, onSelectionChange]);

  useEffect(() => {
    if (onTimeSlotChange) {
      onTimeSlotChange(timeSlots);
    }
  }, [timeSlots, onTimeSlotChange]);

  const columnHeaders = useMemo(() => {
    const headers: { date: string; weekday: string }[] = [];
    const weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const current = new Date(initialStartDate);
    
    if (current.getDay() !== 1) {
      const daysUntilMonday = (1 - current.getDay() + 7) % 7;
      current.setDate(current.getDate() + daysUntilMonday);
    }
    
    for (let i = 0; i < cols; i++) {
      const day = current.getDate();
      const weekdayIndex = (current.getDay() + 6) % 7;
      const weekday = weekdays[weekdayIndex];
      
      headers.push({
        date: `${day}`,
        weekday: weekday,
      });
      current.setDate(current.getDate() + 1);
    }
    return headers;
  }, [initialStartDate, cols]);

  const timeLabels = useMemo(() => {
    const labels: string[] = [];
    for (let i = 0; i < rows; i++) {
      const hour = startHour + i;
      const displayHour = hour % 12 === 0 ? 12 : hour % 12;
      let amPm: string;
      if (hour === 0 || hour === 24) amPm = "AM";
      else if (hour === 12) amPm = "PM";
      else if (hour > 12 && hour < 24) amPm = "PM";
      else amPm = "AM";
      
      labels.push(`${displayHour} ${amPm}`);
      labels.push("");
    }
    return labels;
  }, [rows, startHour]);

  const handleMouseDown = (boxNumber: number) => {
    setIsMouseDown(true);
    setStartBox(boxNumber);
    
    const alreadySelected = selectedBoxes.includes(boxNumber);
    setIsDeselecting(alreadySelected);
    
    setCurrentSelection([boxNumber]);
  };

  const handleMouseEnter = useCallback(
    (boxNumber: number) => {
      if (isMouseDown && startBox !== null) {
        const startRow = Math.floor((startBox - 1) / cols);
        const startCol = (startBox - 1) % cols;
        const endRow = Math.floor((boxNumber - 1) / cols);
        const endCol = (boxNumber - 1) % cols;
        const minRow = Math.min(startRow, endRow);
        const maxRow = Math.max(startRow, endRow);
        const minCol = Math.min(startCol, endCol);
        const maxCol = Math.max(startCol, endCol);
        
        const range: number[] = [];
        for (let row = minRow; row <= maxRow; row++) {
          for (let col = minCol; col <= maxCol; col++) {
            range.push(row * cols + col + 1);
          }
        }
        
        setCurrentSelection(range);
      }
    },
    [isMouseDown, startBox, cols]
  );

  const handleMouseUpGlobal = useCallback(() => {
    if (isMouseDown) {
      setIsMouseDown(false);
      
      if (currentSelection.length > 0) {
        if (isDeselecting) {
          setSelectedBoxes(prev => {
            const newSelected: number[] = [];
            for (let i = 0; i < prev.length; i++) {
              let keepThis = true;
              for (let j = 0; j < currentSelection.length; j++) {
                if (prev[i] === currentSelection[j]) {
                  keepThis = false;
                  break;
                }
              }
              if (keepThis) {
                newSelected.push(prev[i]);
              }
            }
            return newSelected;
          });
        } else {
          setSelectedBoxes(prev => {
            const selectionSet = new Set([...prev, ...currentSelection]);
            return Array.from(selectionSet);
          });
        }
        
        setCurrentSelection([]);
      }
      
      setIsDeselecting(false);
      setStartBox(null);
    }
  }, [isMouseDown, currentSelection, isDeselecting]);

  const combinedSelection = useMemo(() => {
    if (isDeselecting) {
      const currentSet = new Set(currentSelection);
      return selectedBoxes.filter(box => !currentSet.has(box));
    } else {
      return [...new Set([...selectedBoxes, ...currentSelection])];
    }
  }, [selectedBoxes, currentSelection, isDeselecting]);

  useEffect(() => {
    document.addEventListener("mouseup", handleMouseUpGlobal);
    return () => {
      document.removeEventListener("mouseup", handleMouseUpGlobal);
    };
  }, [handleMouseUpGlobal]);

  const timetableContainerStyle: React.CSSProperties = {
    display: "grid",
    gridTemplateColumns: `minmax(30px, 45px) repeat(${cols}, minmax(40px, 1fr))`,
    gridTemplateRows: `auto repeat(${actualRows}, minmax(20px, 1fr))`,
    gap: "1px",
    userSelect: "none",
    width: '100%',
    height: '100%',
    border: "1px solid hsl(var(--sidebar-border))",
  };

  const cellBaseStyle: React.CSSProperties = {
    textAlign: "center",
    fontSize: "0.7rem",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "20px",
    color: "hsl(var(--sidebar-foreground))",
  };

  const headerCellStyle: React.CSSProperties = {
    ...cellBaseStyle,
    fontWeight: "bold",
    flexDirection: "column",
    padding: "4px 2px",
    fontSize: "0.65rem",
  };

  const timeLabelCellStyle: React.CSSProperties = {
    ...cellBaseStyle,
    justifyContent: "flex-end",
    paddingRight: "8px",
    fontSize: "0.65rem",
    minWidth: "45px",
  };

  const emptyTopLeftCellStyle: React.CSSProperties = {
    ...cellBaseStyle,
  };

  return (
    <div className="flex flex-col h-full w-full">
      <div className="flex justify-between items-center mb-3 pb-2 border-b border-ucla-blue/20">
        <h3 className="text-lg font-semibold text-ucla-blue-800">
          Availability
        </h3>
        <button 
          onClick={() => setSelectedBoxes([])} 
          className="text-xs py-2 px-3 bg-ucla-blue/10 hover:bg-ucla-blue/20 
          rounded-md text-ucla-blue-700 transition-colors"
        >
          Reset
        </button>
      </div>
      
      <div className="flex-grow min-h-0"> 
        <div
          style={timetableContainerStyle}
          className="timetable-grid select-none" 
          onMouseLeave={() => {
              if(isMouseDown) setIsMouseDown(false);
          }}
        >
          {/* Top-left empty cell */}
          <div style={{
            ...emptyTopLeftCellStyle, 
            borderRight: "1px solid hsl(var(--sidebar-border))",
            borderBottom: "1px solid hsl(var(--sidebar-border))"
          }}>&nbsp;</div>

          {/* Date/Weekday headers */}
          {columnHeaders.map((header, index) => (
            <div 
              key={`header-${index}`} 
              style={{
                ...headerCellStyle,
                borderRight: index === cols - 1 ? undefined : "1px solid hsl(var(--sidebar-border))",
                borderBottom: "2px solid hsl(var(--ucla-yellow))",
              }}
              className="timetable-header"
            >
              <div>{header.date}</div>
              <div>{header.weekday}</div>
            </div>
          ))}

          {/* Time labels and selectable boxes */}
          {[...Array(rows).keys()].map((hourIndex) => {
            const hourRowIndex = hourIndex * 2;
            return (
            <React.Fragment key={`hour-${hourIndex}`}>
              <div 
                style={{
                  ...timeLabelCellStyle,
                  borderRight: "2px solid hsl(var(--ucla-blue)/30%)",
                  borderBottom: hourIndex === rows - 1 ? undefined : "1px solid hsl(0, 0%, 85%)",
                  gridRow: `span 2`,
                  alignItems: "center",
                }}
                className="timetable-time-label"
              >
                {timeLabels[hourRowIndex]}
              </div>

              {[...Array(cols).keys()].map((colIndex) => {
                const firstHalfBoxNumber = hourRowIndex * cols + colIndex + 1;
                const secondHalfBoxNumber = (hourRowIndex + 1) * cols + colIndex + 1;
                
                const firstHalfSelected = combinedSelection.includes(firstHalfBoxNumber);
                const secondHalfSelected = combinedSelection.includes(secondHalfBoxNumber);
                
                return (
                  <div
                    key={`hour-${hourIndex}-col-${colIndex}`}
                    className="timetable-hour-box"
                    style={{
                      ...cellBaseStyle,
                      gridRow: `span 2`,
                      position: 'relative',
                      padding: 0,
                      display: 'block',
                      borderRight: colIndex === cols - 1 ? undefined : "1px solid hsl(0, 0%, 85%)",
                      borderBottom: hourIndex === rows - 1 ? undefined : "1px solid hsl(0, 0%, 85%)",
                    }}
                  >
                    <div
                      className={`timetable-half-box ${firstHalfSelected ? "timetable-selected" : ""}`}
                      onMouseDown={() => handleMouseDown(firstHalfBoxNumber)}
                      onMouseEnter={() => handleMouseEnter(firstHalfBoxNumber)}
                      role="gridcell"
                      aria-selected={firstHalfSelected}
                      style={{
                        position: 'absolute',
                        top: '1px',
                        left: '1px',
                        right: '2px',
                        bottom: '50%', 
                        cursor: 'pointer',
                        backgroundColor: firstHalfSelected ? 'var(--selection-color, lightblue)' : undefined,
                        zIndex: 2,
                      }}
                    />
                    
                    <div 
                      style={{
                        position: 'absolute',
                        left: 0,
                        right: 0,
                        top: '50%',
                        height: '0px', 
                        borderBottom: '1px dashed hsl(0, 0%, 85%)',
                        zIndex: 3,
                      }}
                    />
                    
                    <div
                      className={`timetable-half-box ${secondHalfSelected ? "timetable-selected" : ""}`}
                      onMouseDown={() => handleMouseDown(secondHalfBoxNumber)}
                      onMouseEnter={() => handleMouseEnter(secondHalfBoxNumber)}
                      role="gridcell"
                      aria-selected={secondHalfSelected}
                      style={{
                        position: 'absolute',
                        top: '50%',
                        left: '1px',
                        right: '2px',
                        bottom: '2px',
                        cursor: 'pointer',
                        backgroundColor: secondHalfSelected ? 'var(--selection-color, lightblue)' : undefined,
                        zIndex: 2,
                      }}
                    />
                  </div>
                );
              })}
            </React.Fragment>
          )})}
        </div>
      </div>
    </div>
  );
};

export default TimeTable;