import React, { useState, useCallback } from "react";

const TimeTable = ({ rows = 15, cols = 7 }) => {
  console.log('TimeTable component rendered'); // Debugging log

  const times = (i, time_start, bool_AM) => {
    let time_bias = Math.floor(i / 7);
    let hour = time_start + time_bias;
    let isPM = bool_AM ? hour >= 12 : hour >= 12;
    let Am_PM = isPM ? "PM" : "AM";

    if (hour % 12 === 0) {
      return "12 " + Am_PM;
    } else {
      return (hour % 12).toString() + " " + Am_PM;
    }
  };

  const [isMouseDown, setIsMouseDown] = useState(false);
  const [selectedBoxes, setselectedBoxes] = useState([]);

  const handleMouseDown = (boxNumber) => {
    setIsMouseDown(true);
    setselectedBoxes([boxNumber]);
  };

  const handleMouseEnter = useCallback(
    (boxNumber) => {
      if (isMouseDown) {
        const startBox = selectedBoxes[0];
        const endBox = boxNumber;
        const startRow = Math.floor((startBox - 1) / cols);
        const startCol = (startBox - 1) % cols;
        const endRow = Math.floor((endBox - 1) / cols);
        const endCol = (endBox - 1) % cols;

        const minRow = Math.min(startRow, endRow);
        const maxRow = Math.max(startRow, endRow);
        const minCol = Math.min(startCol, endCol);
        const maxCol = Math.max(startCol, endCol);

        const selected = [];
        for (let row = minRow; row <= maxRow; row++) {
          for (let col = minCol; col <= maxCol; col++) {
            selected.push(row * cols + col + 1);
          }
        }

        setselectedBoxes(selected);
      }
    },
    [isMouseDown]
  );

  const handleMouseUp = () => {
    setIsMouseDown(false);
  };

  return (
    <div>
      <h1>TimeTable Component</h1>
      <div
        className="grid"
        style={{ "--rows": rows, "--cols": cols }}
        onMouseUp={handleMouseUp}
      >
        {[...Array(rows * cols).keys()].map((i) => (
          <div
            key={i}
            className={`box ${selectedBoxes.includes(i + 1) ? "selected" : ""}`}
            onMouseDown={() => handleMouseDown(i + 1)}
            onMouseEnter={() => handleMouseEnter(i + 1)}
          >
            <h4 className="time-label">{times(i, 8, true)}</h4>
            <div className="half-hour-marker"></div>
          </div>
        ))}
      </div>
      
      <style jsx>{`
        .grid {
          display: grid;
          grid-template-rows: repeat(var(--rows), 1fr);
          grid-template-columns: repeat(var(--cols), 1fr);
          gap: 2px;
        }
        
        .box {
          position: relative;
          border: 1px solid #ccc;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: flex-start;
          padding: 5px;
          height: 60px;
        }
        
        .box.selected {
          background-color: rgba(75, 85, 199, 0.3);
        }
        
        .time-label {
          margin: 0;
          font-size: 0.8rem;
          width: 100%;
          text-align: center;
        }
        
        .half-hour-marker {
          position: absolute;
          width: 90%;
          border-top: 1px dashed #999;
          top: 50%;
          left: 5%;
          pointer-events: none;
        }
      `}</style>
    </div>
  );
};

export default TimeTable;
