function generateSections(existingData = null) {

    const count = parseInt(
        document.getElementById("section_count").value
    );

    const container = document.getElementById("sections-container");
    container.innerHTML = "";

    for (let i = 0; i < count; i++) {

        let sectionData = existingData ? existingData[i] : null;
        let sectionLetter = String.fromCharCode(65 + i);

        const html = `
        <div class="card p-3 mb-3 border">
            <h6 class="mb-3">Section ${sectionLetter}</h6>

            <div class="row g-3">

                <div class="col-md-3">
                    <label class="form-label">Section Label</label>
                    <input type="text"
                           name="section_${i}_name"
                           value="${sectionData ? sectionData.section : sectionLetter}"
                           class="form-control"
                           readonly>
                </div>

                <div class="col-md-3">
                    <label class="form-label">Question Type</label>
                    <select name="section_${i}_type"
                            class="form-select">
                        <option value="mcq"
                            ${sectionData && sectionData.question_type === 'mcq' ? 'selected' : ''}>
                            MCQ
                        </option>
                        <option value="descriptive"
                            ${sectionData && sectionData.question_type === 'descriptive' ? 'selected' : ''}>
                            Descriptive
                        </option>
                    </select>
                </div>

                <div class="col-md-3">
                    <label class="form-label">Marks per Question</label>
                    <input type="number"
                           name="section_${i}_mark"
                           value="${sectionData ? sectionData.mark_per_question : ''}"
                           class="form-control"
                           required>
                </div>

                <div class="col-md-3">
                    <label class="form-label">Number of Questions</label>
                    <input type="number"
                           name="section_${i}_count"
                           value="${sectionData ? sectionData.number_of_questions : ''}"
                           class="form-control"
                           required>
                </div>

            </div>
        </div>
        `;

        container.insertAdjacentHTML("beforeend", html);
    }
}

{% if template and edit_mode %}
document.addEventListener("DOMContentLoaded", function() {
    const existingSections = {{ template.categories | tojson }};
    generateSections(existingSections);
});
{% endif %}