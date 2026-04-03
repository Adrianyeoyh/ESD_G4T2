import axios from "axios";

export const drugApi = axios.create({
  baseURL: '/drug',
  timeout: 15000,
});

export const patientApi = axios.create({
  baseURL: "http://localhost:5003",
  timeout: 15000,
});

export const invoicePaymentApi = axios.create({
  baseURL: '/payments',
  timeout: 15000,
});

export const recordsApi = axios.create({
  baseURL:
    "https://personal-iipxahjd.outsystemscloud.com/ClinicalRecordServices/rest/RecordsAPI/",
  timeout: 15000,
});

export const billingApi = axios.create({
  baseURL: '/make_payment',
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});
