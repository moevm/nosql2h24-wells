
function normalizeRating(rating) {
    let d1 = Math.floor(rating);
    let d2 = Math.floor((rating - d1)*10);

    return ''+d1 + (d2 == 0 ? '' : ','+d2);
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

function generateCourtyardCard(title, address, rating, id) {
    rating = normalizeRating(rating);
    return `<div class="mb-3 advanced-search-card">
                <div class="list-group-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6>${title}</h6>
                            <p class="mb-0 text-muted">${address}</p>
                            <small class="text-warning">★ ${rating}</small>
                        </div>
                        <a href="courtyard.html?id=${id}" class=""><span class="material-icons purple f-24">open_in_new</span></a>
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
                    <a href="profile.html?id=321" class=""><span class="material-icons purple f-24">open_in_new</span></a>
                </div>
            </div>`
}

function generateVisitCard(title, address, rating, visited_at) {
    rating = normalizeRating(rating);
    return `<div class="list-group-item">
                <a href="courtyard.html?id=123" class="link-dark">
                    <h6 class="mb-1 link-dark" id="title">${title}</h6>
                </a>
                <p class="mb-0" id="rating">${address}</p>
                <div class="d-flex justify-content-between">
                    <p class="mb-0">★ <span id="rating">${rating}</span></p>
                    <small class="text-muted">Посетил <span id="visited_at">${visited_at}</span></small>
                </div>
            </div>`
}

function generateReviewCard(username, last_name, first_name, patronymic, visited_at, rating, comment) { 
    rating = normalizeRating(rating);
    return `<div class="list-group-item">
                <div class="d-flex justify-content-between">
                    <h5 class="mb-1">
                        ${username} <span class="text-black-50">aka ${last_name} ${first_name} ${patronymic}</span> <span class="text-warning">${rating} ★</span>
                    </h5>
                    <small>${visited_at}</small>
                </div>
                <p class="mb-1">${comment}</p>
            </div>`
}