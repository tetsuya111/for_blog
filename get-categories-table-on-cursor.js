GET_POST_URL="https://torino2019.com/fanza-capa/wp-json/wp/v2/posts";
GET_THUMB_URL="https://torino2019.com/fanza-capa/wp-json/wp/v2/media/";
//content=`<div class="content get-categories-table" style="position:fixed;right:33%;top:5%;z-index:1;width:40%;height:70%;background-color: transparent;border:none;"></div>`;
content=`<div class="content get-categories-table"></div>`;
//document.write(content);
$(".content").append(content);
let GCT=$(".get-categories-table div");
let GCT_CONTENT=$(".get-categories-table.content");
GCT_CONTENT.hide();
function getThumb(id_){
url=GET_THUMB_URL+id_;
res=null;
$.ajax({
"url":url,
"async":false,
"success":function(data){
res=data;
	}
		});
return res["link"];
}
function toBlogCards(data){
imgid=data["featured_media"];
if(imgid)
thumb=getThumb(imgid);
else
thumb="";
thumb=`<img src="${thumb}" width=150 height=150></img>`;
return '<a class="blogcard-wrap internal-blogcard-wrap a-wrap cf" href="'+data["link"]+'"><div class="blogcard internal-blogcard ib-left cf"><figure class="blogcard-thumbnail internal-blogcard-thumbnail">'+thumb+'</figure><div class="blogcard-content internal-blogcard-content"><div class="blogcard-title internal-blogcard-title">'+data["title"]["rendered"]+'</div><div class="blogcard-snippet internal-blogcard-snippet">'+data["excerpt"]["rendered"]+'</div></div></div></a>`;
return `<a class="blogcard-wrap internal-blogcard-wrap a-wrap cf" href="${data["link"]}"><div class="blogcard internal-blogcard ib-left cf"><figure class="blogcard-thumbnail internal-blogcard-thumbnail">${thumb}</figure><div class="blogcard-content internal-blogcard-content"><div class="blogcard-title internal-blogcard-title">${data["title"]["rendered"]}</div><div class="blogcard-snippet internal-blogcard-snippet">${data["excerpt"]["rendered"]}</div></div></div></a>`;
}
function getPosts(query,callback,n=3){
//$("#yyy").text($("#yyy").text()+"XXY");
params={
"search":query,
"per_page":n
};
//$("#yyy").text($("#yyy").text()+"XXY");
$.getJSON(GET_POST_URL,params,function(data){
//$("#yyy").text($("#yyy").text()+"XXY "+data);
//$("#yyy").text($("#yyy").text()+"XXY "+JSON.stringify(data));
callback(data);
});
}
//$("#xxx").on("mouseover",function(e){
GCT.mouseover(function(e){
	name=$(this).text();
	//GCT_CONTENT.html(name);
	//if(!GCT_CONTENT.html())
	//	return;
	//document.write(name);
	html="";
	getPosts(name,function(data){
	for(key in data){
		blogcard=toBlogCards(data[key]);
		//$("#yyy").html(blogcard);
		console.log(`blogcard : ${blogcard}`);
		html=html+blogcard;
	}
	console.log(`html : ${html}`);
	GCT_CONTENT.html(html);
	GCT_CONTENT.show();
	});
});
$(".get-categories-table").mousedown(function(e){
	GCT_CONTENT.html("");
	GCT_CONTENT.hide();
});
