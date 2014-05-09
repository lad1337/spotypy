

function check_percent(){
    $.getJSON("/percent", function(res){
        if(res.percent < 3)
            check_queue();
        $("nav .progress-bar").css("width", res.percent + "%");
    });
}

function check_queue(){
    var source   = $("#queue-item-template").html();
    var q_template = Handlebars.compile(source);
    var source   = $("#history-item-template").html();
    var h_template = Handlebars.compile(source);
    $.getJSON("/queue", function(results){
        $("#queue").html("<ul></ul>");
        var list = $("#queue ul");
        $.each(results, function(i, item){
            item["full"] = JSON.stringify(item);
            list.append(q_template(item));
        });
        
    });
    $.getJSON("/history", function(results){
        $("#history").html("<ul></ul>");
        var list = $("#history ul");
        $.each(results, function(i, item){
            item["full"] = JSON.stringify(item);
            list.append(h_template(item));
        })
    });
    check_current();
    check_users();
}


function check_current(){
    var source   = $("#current-item-template").html();
    var template = Handlebars.compile(source);
    $.getJSON("/current", function(current){
        $("#current").html(template(current));
    });

}


function check_users(){
    var source   = $("#user-item-template").html();
    var template = Handlebars.compile(source);
    $.getJSON("/users", function(users){
        $("#users").html("");
        $.each(users, function(i, user){
            $("#users").append(template({name: user}));
        });

    });
}


var refresh_interval_percent;
var refresh_interval_queue;
function init_polls(){

    check_percent();
    refresh_interval_percent = window.setInterval(check_percent, 1000);

    check_queue();
    refresh_interval_queue = window.setInterval(check_queue, 20000);
}


$(document).ready(function() {
    init_polls();

    $(".play-pause").click(function(){
        $.get("/pause",function(){});
    });
    $(".stop").click(function(){
        $.get("/stop",check_queue);
    });
    $(".play-prev").click(function(){
        $.get("/prev",check_queue);
    });
    $(".play-next").click(function(){
        $.get("/next",check_queue);
    });
    $(".glyphicon-volume-down").click(function(){
        var volume = parseInt($(".player-control.volume").data("volume"));
        volume -= 5;
        if(volume < 0)
            volume = 0;
        $.post("/status", JSON.stringify({volume: volume}),function(){
            check_queue();
            $(".player-control.volume").data("volume", volume);
        });
    });
    $(".glyphicon-volume-up").click(function(){
        var volume = parseInt($(".player-control.volume").data("volume"));
        volume += 5;
        if(volume >= 100)
            volume = 100;
        $.post("/status", JSON.stringify({volume: volume}),function(){
            check_queue();
            $(".player-control.volume").data("volume", volume);
        });
    });

    $("form.col-md-4").on("submit", function( event ) {
        event.preventDefault();
        var input = $("input", this);
        var user_name = input.val();
        console.log("adding user", user_name);
        $.post("/user", JSON.stringify({user_name: user_name}), function(){
            check_users();
            input.val("");
        });
    });
    $(document).on("click", ".glyphicon-remove-sign", function(){
        $.post("/remove_user", JSON.stringify({user_name: $(this).parent().data("name")}), check_users);
    });

    var source   = $("#search-item-template").html();
    var template = Handlebars.compile(source);

    $("nav form").on("submit", function( event ) {
        event.preventDefault();
        var term = $("input", this).val();
        console.log("searching for", term);
        $.getJSON("/search", {term: term}, function(results){
            $("#search-results").html("<ul></ul>");
            var list = $("#search-results ul");
            $.each(results, function(i, item){
                item["full"] = JSON.stringify(item);
                list.append(template(item));
            })
        })
    });

    $(document).on('click', "#search-results .glyphicon-play, #queue .glyphicon-play, #history .glyphicon-play", function () {
        var item = $(this).parent();
        $.post("/play", JSON.stringify(item.data("full")), check_queue);
    });


    $(document).on('click', "#search-results .glyphicon-plus, #history .glyphicon-plus", function () {
        var item = $(this).parent();
        $.ajax({
          type: "PUT",
          url: "/queue",
          data: JSON.stringify(item.data("full")),
          success: check_queue
        });
    });

});
