var ids = [];
document.querySelector("table").addEventListener('click', function (e) {
    var cell = e.target.closest("td");
    if (cell != null) {
        console.log(cell.id);
    }
    ids.push(cell.id);
    console.log(ids);
    document.getElementById("selected").value = ids;
});

//var submitBut = document.getElementById("submit");
//submitBut.addEventListener("click", listify(ids));