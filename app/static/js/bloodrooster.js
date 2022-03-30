// Bloodrooster javascript for index.html


// globals
var nodes = null;
var edges = null;
var network = null;

// draw a vis.js network given json formatted string containing nodes and edges
function draw(jsonstr='')
{
    var computer_path = "static/images/computer.png";
    var user_path = "static/images/user.png";
    var group_path = "static/images/group.png";
    var unknown_path = "static/images/unknown.png";

    nodes = [];
    edges = [];

    node_font = { size: 12, color: "white", face: "arial" }
    edge_font = { size: 12, color: "white", face: "arial" }

    console.log(jsonstr.length);
    console.log(jsonstr);

    if (jsonstr.length > 0) {
        jsonobj = JSON.parse(jsonstr);
        if (jsonobj != null) {
            // translate nodes json into vis compatible format
            Object.entries(jsonobj.nodes).forEach((entry) => {
                const [key, value] = entry;
                id = value.id;
                label = value.name;
                group = value.group;
                switch(value.type) {
                    case "computer":
                        image = computer_path;
                        break;
                    case "user":
                        image = user_path;
                        break;
                    case "group":
                        image = group_path;
                        break;
                    default:
                        image = unknown_path;
                        break;
                }
                nodes.push({
                    id: id,
                    label: label,
                    title: id,
                    group: group,
                    font: node_font,
                    image: image,
                    shape: "image"
                });
            });

            // translate edges json into vis compatible format
            Object.entries(jsonobj.edges).forEach((entry) => {
                const [key, value] = entry;
                id = value.id;
                from = value.from;
                to = value.to;
                label = value.label;
                edges.push({from: from, to: to, label: label, font: edge_font});
            });
        }
    }

    var data = {
        nodes: nodes,
        edges: edges,
    };

    // reset config element
    var y = document.getElementById("config");
    y.innerHTML = "";

    ////////////////////
    // create a network
    ////////////////////

    var container = document.getElementById("mynetwork");

    var options = {
      physics: {
        stabilization: false,
        hierarchicalRepulsion: {
          avoidOverlap: 1,
        },
      },
      layout: {
        hierarchical: {
            direction: "LR",
            sortMethod: "directed",
        },
      },
      configure: {
        filter: function (option, path) {
          if (path.indexOf("physics") !== -1) {
            return true;
          }
          if (path.indexOf("smooth") !== -1 || option === "smooth") {
            return true;
          }
          return false;
        },
        container: document.getElementById("config"),
      },
    };

    network = new vis.Network(container, data, options);

    //////////////////
    // event handlers
    /////////////////

    network.on("doubleClick", function (params) {
        var test = network.getSelectedNodes()

        if (test.length > 0) {
            console.log(test[0])
            // ajax past to /extended_info to request new graph data
            $.ajax({
                type:'POST',
                url:'/extended_info',
                data: test[0],
                success:function(text) {
                    var y = document.getElementById("extended_info");
                    y.innerHTML = text;
                }
            });
        }
    });

    network.on("oncontext", function (params) {
        params.event.preventDefault();
        $(".custom-menu").finish().toggle(100);
        $(".custom-menu").css({
            top: params.event.pageY + "px",
            left: params.event.pageX + "px"
        });
    });
}

// toggle showing the vis graph advanced options
function showAdvanced() {
    var x = document.getElementById("config");
    var y = document.getElementById("showadvancedbutton");
    if (x.style.display === "none") {
        x.style.display = "block";
        y.innerHTML = "Graph Advanced Settings ↓";
    } else {
        x.style.display = "none";
        y.innerHTML = "Graph Advanced Settings →";
    }
}

// toggle showing the egde toggle options
function showEdgeToggle() {
    var x = document.getElementById("edgetoggle");
    var y = document.getElementById("edgetogglebutton");
    if (x.style.display === "none") {
        x.style.display = "block";
        y.innerHTML = "Edge toggle ↓";
    } else {
        x.style.display = "none";
        y.innerHTML = "Edge toggle →";
    }
}

// toggle showing the loading icon
function showLoading() {
    //<div id="loader" style="display: none;"></div>
    console.log("TESING");
    var y = document.getElementById("mynetwork");
    y.innerHTML = '<div id="loader"></div>';
}

// submit_button handler
function submit_clicked() {
    //e.preventDefault();
    showLoading("block");

    // get checked edges from edgetoggle div

    // package all fields into json object
    var data = {
        'data': $('#src').val(),
        'src': $('#src').val(),
        'dst': $('#dst').val(),
        'edges': create_edge_list(),
        'submit_type': $('#submit_type').val()
    };

    // ajax past to /graph_update to request new graph data
    $.ajax({
        type:'POST',
        url:'/graph_update',
        data: JSON.stringify(data),
        processData: false,
        contentType: "application/json; charset=UTF-8",
        success:function(text) {
            draw(text);
        }
    });
}

// If the menu element is clicked
$(".custom-menu li").click(function(){
    // This is the triggered action name
    switch($(this).attr("data-action")) {

        // A case for each action. Your actions here
        case "info":
            break;
    }

    // Hide it AFTER the action was triggered
    $(".custom-menu").hide(100);
});

function create_edge_list() {
    var edge_list = []

    var ele = document.getElementById("member_check").checked
    if (ele === true) {
        edge_list.push('member');
    }

    ele = document.getElementById("WriteOwner_check").checked
    if (ele === true) {
        edge_list.push('WriteOwner');
    }

    ele = document.getElementById("Owns_check").checked
    if (ele === true) {
        edge_list.push('Owns');
    }

    ele = document.getElementById("GenericWrite_check").checked
    if (ele === true) {
        edge_list.push('GenericWrite');
    }

    ele = document.getElementById("GenericAll_check").checked
    if (ele === true) {
        edge_list.push('GenericAll');
    }

    ele = document.getElementById("AllExtendedRights_check").checked
    if (ele === true) {
        edge_list.push('AllExtendedRights');
    }

    ele = document.getElementById("AddKeyCredentialLink_check").checked
    if (ele === true) {
        edge_list.push('AddKeyCredentialLink');
    }

    ele = document.getElementById("GetChanges_check").checked
    if (ele === true) {
        edge_list.push('GetChanges');
    }

    ele = document.getElementById("GetChangesAll_check").checked
    if (ele === true) {
        edge_list.push('GetChangesAll');
    }

    return edge_list
}

function test_clicked() {
    console.log('ADFHJDHF');

    //network.body.data.nodes.add({ id: 72, label: "one"});
    //network.body.data.nodes.add({ id: 73, label: "two"});
    //network.body.data.nodes.add({ id: 74, label: "three"});
    //network.body.data.nodes.add({ id: 75, label: "four"});

    //network.body.data.edges.add({from: 72, to: 73});
    //network.body.data.edges.add({from: 73, to: 74});
    //network.body.data.edges.add({from: 74, to: 75});
    //network.body.data.edges.add({from: 75, to: "S-1-5-21-3937601378-3721788405-2067139823-1834"});
}