import './App.css';
import TimeTable from './timetable.js';

function App() {
  return (
    <div className="App">
      <TimeTable rows={15} columns={7} />
    </div>
  );
}

export default App;
