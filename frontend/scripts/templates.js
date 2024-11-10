
function normalizeRating(rating) {
    let d1 = Math.floor(rating);
    let d2 = Math.floor((rating - d1)*10);
    return ''+d1+','+d2;
}

function addClass(html_string, classname, selector='advanced-search-card') {
    let parser = new DOMParser();
    let doc = parser.parseFromString(html_string, 'text/html');
    
    let els = doc.getElementsByClassName(selector);
    for (let index = 0; index < els.length; index++)
        els[index].classList.add(classname);

    return doc.documentElement.innerHTML;
}

function addColumnClass(card) {
    return addClass(card, 'col-md-6');
}

function generateCourtyardCard(title, address, rating) {
    rating = normalizeRating(rating);
    return `<div class="mb-3 advanced-search-card">
                <div class="list-group-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6>${title}</h6>
                            <p class="mb-0 text-muted">${address}</p>
                            <small class="text-warning">★ ${rating}</small>
                        </div>
                        <a href="courtyard.html?id=123" class=""><span class="material-icons purple f-24">open_in_new</span></a>
                    </div>
                </div>
            </div>`
}

function generateUserCard(username, last_name, first_name, patronymic, visited) {

    return `<div class="mb-3 advanced-search-card">
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <span>
                        <span class="card-username">${username}</span> 
                        <span class="card-aka">aka ${last_name} ${first_name} ${patronymic}</span>
                        <br>
                        <small class="text-danger">${visited} двора</small>
                    </span>
                    <a href="#" class=""><span class="material-icons purple f-24">open_in_new</span></a>
                </div>
            </div>`
}