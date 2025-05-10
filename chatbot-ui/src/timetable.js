import { useState, useCallback } from "react";
import './timetable.css';

const TimeTable = ({ rows = 15, cols = 7 }) => {
  const times = (i, time_start, bool_AM) => {
    let time_bias = Math.floor (i/7)
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
  const [isDeselecting, setIsDeselecting] = useState(false);
  const [startBox, setStartBox] = useState(null);
  const [selectedBoxes, setSelectedBoxes] = useState([]);

  const handleMouseDown = (boxNumber) => {
    setIsMouseDown(true);
    setStartBox(boxNumber);

    const alreadySelected = (selectedBoxes.indexOf(boxNumber) !== -1)
    setIsDeselecting(alreadySelected);
    setSelectedBoxes((prev) =>
      alreadySelected ? prev.filter((n) => n !== boxNumber) : [...prev, boxNumber]
    );
  };

  const handleMouseEnter = useCallback(
    (boxNumber) => {
      if (isMouseDown && startBox !== null) {
        const startRow = Math.floor((startBox - 1) / cols);
        const startCol = (startBox - 1) % cols;
        const endRow = Math.floor((boxNumber - 1) / cols);
        const endCol = (boxNumber - 1) % cols;

        const minRow = Math.min(startRow, endRow);
        const maxRow = Math.max(startRow, endRow);
        const minCol = Math.min(startCol, endCol);
        const maxCol = Math.max(startCol, endCol);

        const range = [];
        for (let row = minRow; row <= maxRow; row++) {
          for (let col = minCol; col <= maxCol; col++) {
            range.push(row * cols + col + 1);
          }
        }

        setSelectedBoxes((prev) => {
  if (isDeselecting) {
   const newSelected = [];
for (let i = 0; i < prev.length; i++) {
  let keepthis = true;
  for (let j = 0; j < range.length; j++) {
    if (prev[i] === range[j]) {
      keepthis = false;
      break;
    }
  }
  if (keepthis) {
    newSelected.push(prev[i]);
  }
}
return newSelected;

  } else {
    const newBoxes = [...prev];
   for (let i = 0; i < range.length; i++) {
  newBoxes.push(range[i]);
}
    return newBoxes;
  }
});





      }
    },
    [isMouseDown, startBox, isDeselecting, cols]
  );

  const handleMouseUp = () => {
    setIsMouseDown(false);
    setIsDeselecting(false);
    setStartBox(null);
  };

  return (
     <div>
    <div
      className="ttgrid"
      style={{ "--rows": rows, "--cols": cols }}
      onMouseUp={handleMouseUp}
    >
      {[...Array(rows * cols).keys()].map((i) => (
        <h4
          key={i}
          className={`ttbox ${selectedBoxes.includes(i + 1) ? "ttselected" : ""}`}
          onMouseDown={() => handleMouseDown(i + 1)}
          onMouseEnter={() => handleMouseEnter(i + 1)}
        >
          {times(i, 8, true)}
        </h4>
      ))}
      
    </div>
    <br/> <br/>
      <button onClick={() => setSelectedBoxes([])}>Clear</button>
     </div>
  );
};

export default TimeTable;
