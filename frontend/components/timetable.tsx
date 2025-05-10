"use client"; 

import React, { useState, useCallback, useEffect, useMemo } from "react";

interface TimeTableProps {
  rows?: number;
  cols?: number;
  initialStartDate?: Date;
  startHour?: number;
  onSelectionChange?: (selection: number[]) => void;
}

const TimeTable: React.FC<TimeTableProps> = ({
  rows = 15, // This now represents hours, not rows (we'll have 2 rows per hour)
  cols = 7,
  initialStartDate = new Date("2025-05-12"), // Setting it to Monday, May 12, 2025
  startHour = 8, 
  onSelectionChange,
}) => {
  // Double the actual number of rows to account for 30-minute intervals
  const actualRows = rows * 2;
  
  const [isMouseDown, setIsMouseDown] = useState(false);
  const [selectedBoxes, setSelectedBoxes] = useState<number[]>([]);
  // Add a state to track the current selection (before mouseup)
  const [currentSelection, setCurrentSelection] = useState<number[]>([]);
  // Add a state to track whether shift key is pressed
  const [isShiftPressed, setIsShiftPressed] = useState(false);

  // Add event listeners for shift key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Shift') {
        setIsShiftPressed(true);
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.key === 'Shift') {
        setIsShiftPressed(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, []);

  // Report selection changes to parent component if callback is provided
  useEffect(() => {
    if (onSelectionChange) {
      onSelectionChange(selectedBoxes);
    }
  }, [selectedBoxes, onSelectionChange]);

  const columnHeaders = useMemo(() => {
    const headers: { date: string; weekday: string }[] = [];
    // Rearranged to start from Monday
    const weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
    const current = new Date(initialStartDate);
    
    // Ensure we're starting with Monday (day 1)
    if (current.getDay() !== 1) { // Monday is 1 in getDay() (0 is Sunday)
      // Find the closest Monday
      const daysUntilMonday = (1 - current.getDay() + 7) % 7;
      current.setDate(current.getDate() + daysUntilMonday);
    }
    
    for (let i = 0; i < cols; i++) {
      const day = current.getDate();
      const month = current.toLocaleString("default", { month: "short" });
      // Get index in our rearranged weekdays array
      const weekdayIndex = (current.getDay() + 6) % 7; // Transform Sunday (0) to 6, Monday (1) to 0, etc.
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
      
      // Add full hour label
      labels.push(`${displayHour} ${amPm}`);
      
      // Add empty label for half-hour
      labels.push("");
    }
    return labels;
  }, [rows, startHour]);

  const handleMouseDown = (boxNumber: number) => {
    setIsMouseDown(true);
    
    // Start a new selection
    setCurrentSelection([boxNumber]);
  };

  const handleMouseEnter = useCallback(
    (boxNumber: number) => {
      if (isMouseDown) {
        if (currentSelection.length === 0) return;
        
        const startBox = currentSelection[0];
        const endBox = boxNumber;
        const startRow = Math.floor((startBox - 1) / cols);
        const startCol = (startBox - 1) % cols;
        const endRow = Math.floor((endBox - 1) / cols);
        const endCol = (endBox - 1) % cols;
        const minRow = Math.min(startRow, endRow);
        const maxRow = Math.max(startRow, endRow);
        const minCol = Math.min(startCol, endCol);
        const maxCol = Math.max(startCol, endCol);
        
        const selected: number[] = [];
        for (let row = minRow; row <= maxRow; row++) {
          for (let col = minCol; col <= maxCol; col++) {
            selected.push(row * cols + col + 1);
          }
        }
        
        setCurrentSelection(selected);
      }
    },
    [isMouseDown, currentSelection, cols]
  );

  const handleMouseUpGlobal = useCallback(() => {
    if (isMouseDown) {
      setIsMouseDown(false);
      
      // Apply the current selection
      if (currentSelection.length > 0) {
        // INVERTED LOGIC: By default, we ADD to selections.
        // If shift is pressed, we REPLACE the selections.
        if (isShiftPressed) {
          // Shift pressed: Replace existing selection
          setSelectedBoxes(currentSelection);
        } else {
          // Default: Add to existing selection
          setSelectedBoxes(prev => {
            const selectionSet = new Set([...prev, ...currentSelection]);
            return Array.from(selectionSet);
          });
        }
        
        // Clear current selection
        setCurrentSelection([]);
      }
    }
  }, [isMouseDown, currentSelection, isShiftPressed]);

  // Use combined set of boxes for display
  const combinedSelection = useMemo(() => {
    return [...new Set([...selectedBoxes, ...currentSelection])];
  }, [selectedBoxes, currentSelection]);

  useEffect(() => {
    document.addEventListener("mouseup", handleMouseUpGlobal);
    return () => {
      document.removeEventListener("mouseup", handleMouseUpGlobal);
    };
  }, [handleMouseUpGlobal]);

  const timetableContainerStyle: React.CSSProperties = {
    display: "grid",
    gridTemplateColumns: `minmax(30px, 45px) repeat(${cols}, minmax(40px, 1fr))`, // Min width for day columns
    gridTemplateRows: `auto repeat(${actualRows}, minmax(20px, 1fr))`, // Reduced min height for better fit
    gap: "1px",
    userSelect: "none",
    width: '100%', // Grid takes full width of its flex-grow parent
    height: '100%', // Grid takes full height of its flex-grow parent
    border: "1px solid hsl(var(--sidebar-border))", // Outer border for the grid
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
    minWidth: "45px", // Reduced from 60px to 45px
  };

  const emptyTopLeftCellStyle: React.CSSProperties = {
    ...cellBaseStyle,
  };

  return (
    <div className="flex flex-col h-full w-full">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-sm font-medium text-sidebar-foreground flex-shrink-0">
          Availability 
          <span className="text-xs ml-2 text-muted-foreground">(Hold Shift to replace selection)</span>
        </h3>
        <button 
          onClick={() => setSelectedBoxes([])} 
          className="text-xs py-1 px-2 bg-sidebar-foreground/10 hover:bg-sidebar-foreground/20 rounded text-muted-foreground hover:text-foreground transition-colors"
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
                borderBottom: "1px solid hsl(var(--sidebar-border))"
              }}
            >
              <div>{header.date}</div>
              <div>{header.weekday}</div>
            </div>
          ))}

          {/* Time labels and selectable boxes, now by hour instead of half-hour */}
          {[...Array(rows).keys()].map((hourIndex) => {
            const hourRowIndex = hourIndex * 2; // Convert hour index to actual row index
            return (
            <React.Fragment key={`hour-${hourIndex}`}>
              {/* Time label for the hour */}
              <div 
                style={{
                  ...timeLabelCellStyle, 
                  borderRight: "1px solid hsl(var(--sidebar-border))",
                  borderBottom: hourIndex === rows - 1 ? undefined : "1px solid hsl(var(--sidebar-border))",
                  // Make it taller to accommodate both 30-min slots
                  gridRow: `span 2`,
                  // Center content vertically
                  alignItems: "center",
                }}
              >
                {timeLabels[hourRowIndex]} {/* First label of the pair */}
              </div>

              {/* Full-hour row with two half-hour boxes in each column */}
              {[...Array(cols).keys()].map((colIndex) => {
                // Calculate box numbers for both half-hour slots
                const firstHalfBoxNumber = hourRowIndex * cols + colIndex + 1;
                const secondHalfBoxNumber = (hourRowIndex + 1) * cols + colIndex + 1;
                
                // Check if boxes are in the combined selection
                const firstHalfSelected = combinedSelection.includes(firstHalfBoxNumber);
                const secondHalfSelected = combinedSelection.includes(secondHalfBoxNumber);
                
                return (
                  <div
                    key={`hour-${hourIndex}-col-${colIndex}`}
                    className="timetable-hour-box"
                    style={{
                      ...cellBaseStyle,
                      gridRow: `span 2`, // Make the box span 2 rows
                      position: 'relative', // For positioning the half-hour divider
                      padding: 0, // Remove padding to allow for inner divs
                      display: 'block', // Override flex to allow for inner content positioning
                      borderRight: colIndex === cols - 1 ? undefined : "1px solid hsl(var(--sidebar-border))",
                      borderBottom: hourIndex === rows - 1 ? undefined : "1px solid hsl(var(--sidebar-border))",
                    }}
                  >
                    {/* First 30-minute slot */}
                    <div
                      className={`timetable-half-box ${firstHalfSelected ? "timetable-selected" : ""}`}
                      onMouseDown={() => handleMouseDown(firstHalfBoxNumber)}
                      onMouseEnter={() => handleMouseEnter(firstHalfBoxNumber)}
                      role="gridcell"
                      aria-selected={firstHalfSelected}
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        bottom: '50%',
                        cursor: 'pointer',
                        backgroundColor: firstHalfSelected ? 'var(--selection-color, lightblue)' : undefined,
                      }}
                    />
                    
                    {/* Dashed line separator */}
                    <div 
                      style={{
                        position: 'absolute',
                        left: 0,
                        right: 0,
                        top: '50%',
                        height: '1px',
                        borderBottom: '1px dashed hsl(var(--sidebar-border))',
                        zIndex: 1,
                      }}
                    />
                    
                    {/* Second 30-minute slot */}
                    <div
                      className={`timetable-half-box ${secondHalfSelected ? "timetable-selected" : ""}`}
                      onMouseDown={() => handleMouseDown(secondHalfBoxNumber)}
                      onMouseEnter={() => handleMouseEnter(secondHalfBoxNumber)}
                      role="gridcell"
                      aria-selected={secondHalfSelected}
                      style={{
                        position: 'absolute',
                        top: '50%',
                        left: 0,
                        right: 0,
                        bottom: 0,
                        cursor: 'pointer',
                        backgroundColor: secondHalfSelected ? 'var(--selection-color, lightblue)' : undefined,
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

// Add this to your CSS or define a CSS variable for selection color
// --selection-color: lightblue;

export default TimeTable;