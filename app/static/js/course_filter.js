document.addEventListener('DOMContentLoaded', () => {
  const deptSelect = document.getElementById('departmentSelect')
  const courseSelect = document.getElementById('courseSelect')

  if (!deptSelect || !courseSelect) return

  deptSelect.addEventListener('change', async () => {
    const deptId = deptSelect.value

    courseSelect.innerHTML = '<option value="">Select course</option>'
    courseSelect.disabled = true

    if (!deptId) return

    try {
      const response = await fetch(
        `/api/courses/by-department?department_id=${deptId}`
      )
      const courses = await response.json()

      courses.forEach(course => {
        const option = document.createElement('option')
        option.value = course.id
        option.textContent = `${course.code} — ${course.title}`
        courseSelect.appendChild(option)
      })

      courseSelect.disabled = false
    } catch (err) {
      console.error('Failed to load courses', err)
    }
  })
})
