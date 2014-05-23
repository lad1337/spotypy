

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
        if(!current["cover_url"])
            $("#cover").css("background-image", "");
        else
            $("#cover").css("background-image", "url('"+ current["cover_url"]+ "')");
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

function render_favs(){
    $("#favorites").html("<ul></ul>");
    var list = $("#favorites ul");
    var favs = JSON.parse(localStorage.getItem("favs"));
    if(!favs){
        $("#favorites").parent().hide();
        return;
    }else{
        $("#favorites").parent().show();
    }

    var source   = $("#favorites-item-template").html();
    var template = Handlebars.compile(source);
    $.each(favs, function(i, fav){
        fav["full"] = JSON.stringify(fav);
        list.append(template(fav));
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

function is_song_in_list(uuid, list){
    for (index = 0; index < list.length; ++index) {
        if(list[index]["uuid"] == uuid){
            return true;
        }
    }
    return false;
}

function set_mark_request(element){
    element.addClass("mark");
}

function remove_mark_request(element){
    element.removeClass("mark");
}


$(document).ready(function() {
    init_polls();

    $(".play-pause").click(function(){
        var icon = $(this);
        set_mark_request(icon);
        $.get("/pause",function(){check_queue(); remove_mark_request(icon);});
    });
    $(".stop").click(function(){
        var icon = $(this);
        set_mark_request(icon);
        $.get("/stop",function(){check_queue(); remove_mark_request(icon);});
    });
    $(".play-prev").click(function(){
        var icon = $(this);
        set_mark_request(icon);
        $.get("/prev",function(){check_queue(); remove_mark_request(icon);});
    });
    $(".play-next").click(function(){
        var icon = $(this);
        console.log("next", icon);
        set_mark_request(icon);
        $.get("/next",function(){check_queue(); remove_mark_request(icon);});
    });
    $(".glyphicon-volume-down").click(function(){
        var icon = $(this);
        set_mark_request(icon);
        var volume = parseInt($(".player-control.volume").data("volume"));
        volume -= 5;
        if(volume < 0)
            volume = 0;
        $.post("/status", JSON.stringify({volume: volume}),function(){
            check_queue();
            $(".player-control.volume").data("volume", volume);
            remove_mark_request(icon);
        });
    });
    $(".glyphicon-volume-up").click(function(){
        var icon = $(this);
        set_mark_request(icon);
        var volume = parseInt($(".player-control.volume").data("volume"));
        volume += 5;
        if(volume >= 100)
            volume = 100;
        $.post("/status", JSON.stringify({volume: volume}),function(){
            check_queue();
            $(".player-control.volume").data("volume", volume);
            remove_mark_request(icon);
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
        var button = $("button", this);
        set_mark_request(button);
        console.log("searching for", term);
        $.getJSON("/search", {term: term}, function(results){
            $("#search-results").html("<ul></ul>");
            var list = $("#search-results ul");
            $.each(results, function(i, item){
                item["full"] = JSON.stringify(item);
                list.append(template(item));
            });

            remove_mark_request(button);
        })
    });

    $(document).on('click', "#search-results .glyphicon-play, #queue .glyphicon-play, #history .glyphicon-play, #favorites .glyphicon-play", function () {
        var icon = $(this);
        var item = icon.parent();
        set_mark_request(icon);
        $.post("/play", JSON.stringify(item.data("full")), function(){check_queue(); remove_mark_request(icon);});
    });
	
    $(document).on('click', "#queue .glyphicon-arrow-up", function() {
        var icon = $(this);
        var item = icon.parent();
	$.ajax({
            type: "PUT", 
            url: "/voteup", 
            data: JSON.stringify(item.data("full")), 
            success: function(){check_queue();}
        });
    });

    $(document).on('click', "#queue .glyphicon-arrow-down", function() {
        var icon = $(this);
        var item = icon.parent();
	$.ajax({
            type: "PUT", 
            url: "/votedown", 
            data: JSON.stringify(item.data("full")), 
            success: function(){check_queue();}
        });
    });

    $(document).on('click', ".glyphicon-star", function () {
        var item = $(this).parent();
        var data = item.data("full");
        var favs = JSON.parse(localStorage.getItem("favs"));
        if(!favs){
            favs = [];
        }
        if(is_song_in_list(data["uuid"], favs))
            return;
        favs.push(data);
        localStorage.setItem("favs", JSON.stringify(favs));
        render_favs();
    });

    $(document).on('click', ".glyphicon-minus", function () {
        var item = $(this).parent();
        var data = item.data("full");
        var favs = JSON.parse(localStorage.getItem("favs"));
        if(!favs){
            return;
        }
        var new_favs = [];
        $.each(favs, function(i, fav){
            if(data["uuid"] != fav["uuid"]){
                new_favs.push(fav);
            }
        });
        localStorage.setItem("favs", JSON.stringify(new_favs));
        render_favs();
    });


    $(document).on('click', ".glyphicon-plus", function () {
        var item = $(this).parent();
        $.ajax({
          type: "PUT",
          url: "/queue",
          data: JSON.stringify(item.data("full")),
          success: check_queue
        });
    });
    render_favs();

});
