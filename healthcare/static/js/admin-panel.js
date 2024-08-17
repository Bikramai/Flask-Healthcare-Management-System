var overview = document.getElementById('overview');
        var analysis = document.getElementById('analysis');

        function overview_change(){
            overview.style.background = "white";
            analysis.style.background = "none";
         }

         function analysis_change(){
            overview.style.background = "none";
            analysis.style.background = "white";
         }

         overview.addEventListener("click", overview_change);
         analysis.addEventListener("click", analysis_change);

         var search = document.getElementById('search');
         var active = document.getElementById('active');

         function search_(){
            active.style.background = "none";
         }

         function active_(){
            active.style.background = "#11C7CC";
         }

         search.addEventListener("click", search_);
         active.addEventListener("click", active_);

