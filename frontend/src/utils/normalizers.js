export const getDrugId = (drug) =>
  Number(drug?.drugId ?? drug?.drug_id ?? drug?.Id ?? drug?.id ?? 0)

export const normalizeDrug = (drug) => {
  const normalizedId = getDrugId(drug)
  const normalizedQuantity = Number(drug?.quantity ?? drug?.stock ?? 0)
  const normalizedPrice = Number(drug?.price ?? 0)
  const normalizedDosage = String(
    drug?.dosage ?? drug?.recommendedDosage ?? drug?.recommended_dosage ?? '',
  ).trim()
  return {
    ...drug,
    id: normalizedId,
    drugId: normalizedId,
    name: drug?.name ?? drug?.drugName ?? drug?.drug_name ?? '',
    drugName: drug?.name ?? drug?.drugName ?? drug?.drug_name ?? '',
    quantity: Number.isFinite(normalizedQuantity) ? normalizedQuantity : 0,
    price: Number.isFinite(normalizedPrice) ? normalizedPrice : 0,
    purpose: String(drug?.purpose ?? '').trim(),
    dosage: normalizedDosage,
    recommendedDosage: normalizedDosage,
    remarks: String(drug?.remarks ?? '').trim(),
  }
}

export const normalizeArrayResponse = (payload) => {
  if (Array.isArray(payload)) return payload
  for (const key of ['data', 'items', 'records', 'Records', 'result']) {
    if (Array.isArray(payload?.[key])) return payload[key]
  }
  return []
}

export const normalizeObjectArrayResponse = (payload) => {
  if (Array.isArray(payload)) return payload
  for (const key of ['data', 'items', 'records', 'result', 'value']) {
    if (Array.isArray(payload?.[key])) return payload[key]
  }
  return []
}

export const normalizeRecord = (record, idx) => {
  const id = record.Id ?? record.id ?? idx + 1
  const patientId = record.patientId ?? record.PatientId ?? null
  const visitNotes = record.VisitNotes ?? record.visitNotes ?? record.notes ?? ''
  const date = record.date ?? record.Date ?? record.visitDate ?? record.VisitDate ?? ''
  const isClosed = Boolean(record.isClosed ?? record.IsClosed ?? false)
  const statusRaw = String(record.status ?? record.Status ?? '').toUpperCase().trim()

  return {
    ...record,
    Id: Number(id),
    patientId: patientId !== null ? String(patientId).trim() : null,
    date,
    VisitNotes: String(visitNotes),
    isClosed,
    patientName: record.patientName ?? record.PatientName ?? record.name ?? 'Unknown patient',
    nric: record.nric ?? record.NRIC ?? record.Nric ?? 'N/A',
    email: record.email ?? record.Email ?? '',
    status: statusRaw || (isClosed ? 'CLOSED' : 'OPEN'),
  }
}

export const normalizeConsultationDrug = (drug, idx) => ({
  id: Number(drug.drugId ?? drug.id ?? drug.Id ?? idx + 1),
  name:
    String(
      drug.drugName ?? drug.name ?? drug.DrugName ?? drug.drug_name ?? 'Unnamed Drug',
    ).trim() || 'Unnamed Drug',
  quantity: Math.max(0, Number(drug.quantity ?? drug.stock ?? drug.Quantity ?? 0)),
  price: Number(drug.price ?? drug.Price ?? 0),
  raw: drug,
})

export const normalizePrescriptionRows = (rows) =>
  rows.map((row, idx) => ({
    id: row.id ?? row.Id ?? row.prescriptionId ?? row.PrescriptionId ?? idx + 1,
    drugName: row.drugName ?? row.DrugName ?? row.medicationName ?? row.MedicationName ?? 'N/A',
    quantity: row.quantity ?? row.Quantity ?? row.qty ?? row.Qty ?? 'N/A',
    dosage: row.dosage ?? row.Dosage ?? row.instructions ?? row.Instructions ?? 'N/A',
    date: row.date ?? row.Date ?? row.createdAt ?? row.CreatedAt ?? 'N/A',
    raw: row,
  }))

export const parseErrorMessage = (error, fallbackMessage) => {
  if (String(error?.message || '').toLowerCase() === 'network error') {
    return `${fallbackMessage} Service may be down or blocked by CORS.`
  }
  const data = error?.response?.data
  if (typeof data === 'string' && data.trim()) return data.trim()
  for (const key of ['message', 'error', 'details']) {
    const candidate = data?.[key]
    if (typeof candidate === 'string' && candidate.trim()) return candidate.trim()
  }
  return error?.message || fallbackMessage
}
