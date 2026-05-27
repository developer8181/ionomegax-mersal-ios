import { createContext, useContext, useReducer, useCallback } from 'react';
import { initialJobs, clients as initialClients } from '../data/initialData';

const AppContext = createContext(null);

const generateId = () => Math.random().toString(36).substr(2, 9);

function appReducer(state, action) {
  switch (action.type) {
    case 'ADD_JOB':
      return {
        ...state,
        jobs: [{ ...action.payload, id: generateId(), createdAt: new Date().toISOString() }, ...state.jobs],
      };

    case 'UPDATE_JOB':
      return {
        ...state,
        jobs: state.jobs.map(job =>
          job.id === action.payload.id ? { ...job, ...action.payload } : job
        ),
      };

    case 'DELETE_JOB':
      return {
        ...state,
        jobs: state.jobs.filter(job => job.id !== action.payload),
      };

    case 'UPDATE_JOB_STATUS': {
      const updates = { status: action.payload.status };
      if (action.payload.status === 'completed') {
        updates.completedAt = new Date().toISOString();
      }
      return {
        ...state,
        jobs: state.jobs.map(job =>
          job.id === action.payload.id ? { ...job, ...updates } : job
        ),
      };
    }

    case 'REORDER_QUEUE': {
      const { dragIndex, hoverIndex } = action.payload;
      const queuedJobs = state.jobs.filter(j => j.status === 'queued');
      const otherJobs = state.jobs.filter(j => j.status !== 'queued');
      const dragJob = queuedJobs[dragIndex];
      const newQueued = [...queuedJobs];
      newQueued.splice(dragIndex, 1);
      newQueued.splice(hoverIndex, 0, dragJob);
      return { ...state, jobs: [...otherJobs, ...newQueued] };
    }

    case 'ADD_CLIENT':
      return {
        ...state,
        clients: [{ ...action.payload, id: generateId(), totalOrders: 0, totalSpent: 0 }, ...state.clients],
      };

    case 'UPDATE_CLIENT':
      return {
        ...state,
        clients: state.clients.map(c =>
          c.id === action.payload.id ? { ...c, ...action.payload } : c
        ),
      };

    case 'DELETE_CLIENT':
      return {
        ...state,
        clients: state.clients.filter(c => c.id !== action.payload),
      };

    case 'SET_NOTIFICATION':
      return {
        ...state,
        notification: action.payload,
      };

    case 'CLEAR_NOTIFICATION':
      return {
        ...state,
        notification: null,
      };

    default:
      return state;
  }
}

const initialState = {
  jobs: initialJobs,
  clients: initialClients,
  notification: null,
};

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  const notify = useCallback((message, type = 'success') => {
    dispatch({ type: 'SET_NOTIFICATION', payload: { message, type } });
    setTimeout(() => dispatch({ type: 'CLEAR_NOTIFICATION' }), 3000);
  }, []);

  return (
    <AppContext.Provider value={{ state, dispatch, notify }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used within AppProvider');
  return context;
}
