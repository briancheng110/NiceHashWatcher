cd "C:\Users\Brian\Desktop\Mining tools\NiceHashLiveMonitoring"

import delim out.csv, clear

drop in  1/539

gen sub = substr(v1,1, 19 )

gen time = clock(sub, "YMDhms")

ren v2 algo
ren v3 status
ren v4 speed
ren v5 limit
ren v6 fmv
ren v7 price_ratio

order time
drop v1 sub v8

quietly count
local total = r(N)

quietly count if status == "idle"
local idle_time = 100* r(N) / `total'

quietly count if status == "working"
local working_time = 100*r(N) / `total'

quietly count if status == "leaking"
local leaking_time = 100*r(N) / `total'

quietly total speed
local sum_speed = e(b)[1,1]

quietly total speed if status == "working"
local working_sum_speed = e(b)[1,1]

local leaking_sum_speed = `sum_speed' - `working_sum_speed'

gen overall_pr_avg = speed / `sum_speed' * price_ratio

quietly total overall_pr_avg
local pr_avg = e(b)[1,1]

gen working_pr_avg = speed / `working_sum_speed' * price_ratio if status == "working"
quietly total working_pr_avg
local working_pr_avg = e(b)[1,1]

gen leaking_pr_avg = speed / `leaking_sum_speed' * price_ratio if status == "leaking"
quietly total leaking_pr_avg
local leaking_pr_avg = e(b)[1,1]

disp "% time in idle, working, and leak"
disp %4.1f `idle_time', %4.1f `working_time', %4.1f `leaking_time'
disp %5.4f `pr_avg', %5.4f `working_pr_avg', %5.4f `leaking_pr_avg'

