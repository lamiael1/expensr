

const API_BASE_URL =

  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";



async function request(endpoint) {

  const response = await fetch(`${API_BASE_URL}${endpoint}`);



  if (!response.ok) {

    throw new Error(`Error HTTP ${response.status}`);

  }



  return response.json();

}



export function getMonitorOverview() {

  return request("/monitor/overview");

}



export function getExpenses() {

  return request("/expenses/");

}

