import { createSlice } from "@reduxjs/toolkit";

const patientsSlice = createSlice({
  name: "patients",
  initialState: {
    list: [],
    activePatientId: null,
    loading: false,
    error: null,
  },
  reducers: {
    setPatients: (state, action) => {
      state.list = action.payload;
      state.loading = false;
      state.error = null;
    },
    setActivePatient: (state, action) => {
      state.activePatientId = action.payload;
    },
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
      state.loading = false;
    },
  },
});

export const { setPatients, setActivePatient, setLoading, setError } = patientsSlice.actions;
export default patientsSlice.reducer;