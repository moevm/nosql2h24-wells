
function normalizeRating(rating) {
    let d1 = Math.floor(rating);
    let d2 = Math.floor((rating - d1)*10);
    return ''+d1+','+d2;
}

function generateCourtyardCard(label, address, rating) {
    rating = normalizeRating(rating);
    return `<div class="col-md-6 mb-3 advanced-search-card">
                <div class="list-group-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <h6>`+label+`</h6>
                            <p class="mb-0 text-muted">`+address+`</p>
                            <small class="text-warning">★ `+rating+`</small>
                        </div>
                        <a href="#" class="btn btn-outline-secondary btn-sm">
                            <i class="fas fa-external-link-alt"></i>
                        </a>
                    </div>
                </div>
            </div>`
}

function generateUserCard(username, last_name, first_name, patronymic, visited) {

    return `<div class="col-md-6 mb-3 advanced-search-card">
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    <span>
                        <span class="card-username">`+username+`</span> 
                        <span class="card-aka">aka `+last_name+" "+first_name+" "+patronymic+" "+`</span>
                        <br>
                        <small class="text-danger">`+visited+` двора</small>
                    </span>
                    <a href="#" class=""><span class="material-icons purple f-24">open_in_new</span></a>
                </div>
            </div>`
}