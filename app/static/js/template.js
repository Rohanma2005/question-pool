function generateSections() {

    const count = parseInt(
        document.getElementById("section_count").value
    );

    const container = document.getElementById("sections-container");
    container.innerHTML = "";

    for (let i = 0; i < count; i++) {

        const html = `
        <div class="card p-3 mb-3">
            <h6>Section ${String.fromCharCode(65 + i)}</h6>

            <div class="row">
                <div class="col">
                    <input type="text"
                        name="section_${i}_name"
                        value="${String.fromCharCode(65 + i)}"
                        class="form-control"
                        readonly>
                </div>

                <div class="col">
                    <select name="section_${i}_type"
                            class="form-select">
                        <option value="mcq">MCQ</option>
                        <option value="descriptive">Descriptive</option>
                    </select>
                </div>

                <div class="col">
                    <input type="number"
                        name="section_${i}_mark"
                        placeholder="Marks per question"
                        class="form-control"
                        required>
                </div>

                <div class="col">
                    <input type="number"
                        name="section_${i}_count"
                        placeholder="Number of questions"
                        class="form-control"
                        required>
                </div>
            </div>
        </div>
        `;

        container.insertAdjacentHTML("beforeend", html);
    }
}