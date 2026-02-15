document.addEventListener('DOMContentLoaded', () => {
    const deptSelect = document.getElementById('courseFilterDept')
    const tableBody = document.getElementById('coursesTableBody')

    if (!deptSelect || !tableBody) return

    deptSelect.addEventListener('change', async () => {
        const deptId = deptSelect.value

        let url = '/api/courses'
        if (deptId) {
            url += `?department_id=${deptId}`
        }

        try {
            const response = await fetch(url)

            if (!response.ok) {
                console.error("API error:", response.status)
                return
            }

            const courses = await response.json()  // ✅ FIXED

            if (!Array.isArray(courses)) {
                console.error("Expected array but got:", courses)
                return
            }

            tableBody.innerHTML = ''

            courses.forEach(course => {
                const row = document.createElement('tr')

                row.innerHTML = `
                    <td>${course.code}</td>
                    <td>${course.title}</td>
                    <td>${course.department}</td>
                    <td class="d-flex gap-2">
                        <a href="/superadmin/courses/${course.id}" class="btn btn-sm btn-outline-primary">
                            View
                        </a>
                    </td>
                `

                tableBody.appendChild(row)
            })

        } catch (err) {
            console.error('Failed to load courses', err)
        }
    })
})
