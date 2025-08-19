import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import LocationSuggest from "./pages/LocationSuggest";

const AppRoutes = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
         <Route path="/locationsuggest" element={<LocationSuggest />} />
      </Routes>
    </Router>
  );
};

export default AppRoutes;
