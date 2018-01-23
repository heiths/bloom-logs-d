const _url = "/search";
let _data;
let search_btn = $('#search_btn');
let object_input = $('#obj_input');


// Search and handle response
function search(e) {
    $(e.target).prop('disabled', true);
    _data = {
        "object": [
            object_input.val()
        ]
    };
    $.ajax({
        type: "POST",
        contentType: "application/json",
        url: _url,
        data: JSON.stringify(_data),
        processData: false,
        success: _success,
        dataType: "json"
    })
}

function _success(data) {
    switch (data.state) {
        case "MISSING":
            flash_alert(`${data.result}`, "info");
            search_btn.prop("disabled", false);
            break;
        case "FAILURE":
            flash_alert(`${data.result}`, "danger");
            search_btn.prop("disabled", false);
            break;
        default:
            performance.mark(`${data.task_id}-start`);
            search_btn.prop('disabled', true);
            $("#result").html("");
            flash_alert(`Fetching result from: <strong>${data.result.recent_log}</strong>\n`, "success", true);
            check_job_status(data.task_id);
    }
}

function check_job_status(task_id) {
    $.getJSON(`/tasks/${task_id}`, function (data) {
        console.log(data);
        switch (data.state) {
            case "UNKNOWN":
                flash_alert(`${data.result}`, "danger");
                search_btn.prop("disabled", false);
                break;
            case "INVALID":
                flash_alert(`${data.result}`, "danger");
                search_btn.prop("disabled", false);
                break;
            case "SUCCESS":
                remove_alerts();
                updatePage(data.result.result);
                search_btn.prop("disabled", false);
                showPerformance(task_id);
                performance.mark(`${task_id}-end`);
                break;
            case "FAILURE":
                flash_alert(`Job failed: ${ data.result}`, "danger");
                break;
            default:
                // PENDING
                setTimeout(function () {
                    check_job_status(task_id);
                }, 1500);
                console.log(data)
        }
    });
}

//Update the page
function flash_alert(message, category, clean) {
    if (typeof(clean) === "undefined") clean = true;
    if (clean) {
        remove_alerts();
    }
    let htmlString = `<div class="alert alert-${category}" role="alert">${message}</div>`;
    console.log(htmlString);
    $(htmlString).appendTo("#messages").fadeIn();
    search_btn.prop('disabled', false);
}

function remove_alerts() {
    $(".alert").fadeOut("slow", function () {
        $(this).remove();
    });
}

function updatePage(result) {
    $(function () {
        $("#result").JSONView(result);
    });
    let overview_html = get_display_overview(result);
    $(overview_html).appendTo("#performanceResult").fadeIn();
}

function get_display_overview(result) {
    console.log(result[0].timestamp);
    if (result[0].timestamp) {
        return ` <div class="displayInfo" role="alert">
    Log is ${timeAgo(result[0].timestamp)}
    </div>`
    } else {
        console.log(`result.timestamp expected (as string)\nGot: ${result[0].timestamp}`)
    }
}

function showPerformance(task_id) {
    $(".perf").fadeOut("slow", function () {
        $(this).remove();
    });
    performance.mark(`${task_id}-end`);

    performance.measure(
        `${task_id}-perf`,
        `${task_id}-start`,
        `${task_id}-end`
    );

    let measures = performance.getEntriesByName(`${task_id}-perf`);
    let measure = measures[0];
    let seconds = parseFloat(measure.duration / 1000).toFixed(2);

    console.log("setTimeout milliseconds:", measure.duration);

    $("#performanceResult").innerText = measures[0];
    let htmlString = `<div class="perf" role="alert">Total time for search: <strong>${seconds}</strong></div>`;
    $(htmlString).appendTo("#performanceResult").fadeIn();
}


// Events
search_btn.on('click', search);
$('#help_btn').on('click', function (e) {
    search_btn.prop("disabled", false);
    let objs = [
        "/v1/MossoCloudFS_a6e6683e-f5c4-41a7-bbb4-2668ecff8a7d/replay121/570/3407612689_1978025109.dem.bz2",
        "MossoCloudFS_7e26876b-2af8-40ea-be59-183972fef36a/fusion_assets/tours/845823/images/thumbnail/0_31505000_1502991092.jpg",
        "/v1/MossoCloudFS_c338b29c-9561-44ce-88a7-45ea61bfa719/NEO_RETS_2014/IMG-47480410_32.jpg",
        "/v1/MossoCloudFS_086f5edf-22c0-4073-9505-e3b70ba63ce3/zilek_minipics/184186321_8.jpg",
        "/v1/MossoCloudFS_e328ea1d-40bd-4e75-af39-3c726d432dbf/sa-originals/12866-r.gif",
        "/v1/MossoCloudFS_e328ea1d-40bd-4e75-af39-3c726d432dbf/sa-originals/6469-r.gif",
        "MossoCloudFS_95358470-4cbb-41c2-a9ee-f8e07319d947/Textiles/small/21685.jpg",
    ];
    let randObj = objs[Math.floor(Math.random() * objs.length)];
    object_input.val(randObj);
});

object_input.on("input", function () {
    let is_empty = (object_input.val().length === 0);
    search_btn.prop("disabled", is_empty);

});


// Helpers
function timeAgo(d) {
    let current = Date.now();
    let msPerMinute = 60 * 1000;
    let msPerHour = msPerMinute * 60;
    let msPerDay = msPerHour * 24;
    let msPerMonth = msPerDay * 30;
    let msPerYear = msPerDay * 365;

    if (typeof d === "string") {
        d = new Date(d);
    }

    let elapsed = current - d;

    if (elapsed < msPerHour) {
        return `${Math.round(elapsed / msPerMinute)} minutes old`;
    }
    else if (elapsed < msPerDay) {
        return `${Math.round(elapsed / msPerHour)} hours old`;
    }
    else if (elapsed < msPerMonth) {
        return `~${Math.round(elapsed / msPerDay)} days old`;
    }
    else if (elapsed < msPerYear) {
        return `~${Math.round(elapsed / msPerMonth)} months old`;
    }
    else {
        return `~${Math.round(elapsed / msPerYear)} years old`;
    }
}
