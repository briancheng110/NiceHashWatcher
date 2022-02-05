local Coins = "dash hns erg xmr btc ae eth beam zec btg cfx rvn bcd bch bsv"
local Days = 5
local Coin_to_analyze = "rvn"
local funding_time_efficiency = 0.6 // estimated % of speed limit that is reached when funded
local magic_number = 659670 // empirically determined exchange rate:market price ratio for breakeven

import delim using "C:\Users\Brian\Desktop\Mining tools\NiceHashWatcher\Old\Output_old.csv", varn(1) clear numericcols(2/197)
drop if time == "Time"
drop v197

quietly count
local total_obs = r(N)

// bc stata freaks out if we try to replace
gen time2 = clock(time, "MD20Yhms")
drop time
ren time2 time
order time

// generate market price tiers and speed limit adjustments
quietly summarize `Coin_to_analyze'_marketprice

local max_price = round(r(max), 0.0001)
local min_price = round(r(min), 0.0001)
// local max_price = r(max)
// local min_price = r(min)

disp `max_price', `min_price'

local Number_of_tiers = (`max_price' - `min_price') / 0.0001

disp `Number_of_tiers'

/*
forvalues tier = `min_price'(0.001)`max_price' {
	quietly count if `Coin_to_analyze'_marketprice < `tier'
	local funded_obs = r(N)
	
	local funded_time_pct = 100 * `funded_obs' / `total_obs'
	local min_sale_price = `tier' / `magic_number'
	local hashrate_speed_limit = 10^4 * (1/`Days') / `funded_time_pct' / `funding_time_efficiency'
	//if `hashrate_speed_limit' < 1000 {
		disp %5.4f `tier', %4.1f `funded_time_pct', %10.8f `min_sale_price', %3.1f `hashrate_speed_limit', %9.4f (0.006 / `tier' * `hashrate_speed_limit' / 100), %9.6f (0.006 / `tier')
	//}
}
*/


foreach Coin of local Coins {
	gen `Coin'_profitpct = 100 * `Coin'_profitbtc / 0.005
	//calculate relationship between network hashrate and difficulty
	quietly regress `Coin'_networkhashrate `Coin'_difficulty
	gen `Coin'_fmv = ((1000000000000)/(`Coin'_difficulty*e(b)[1,1] + e(b)[1,2]))*(24*60*2500)*`Coin'_exchangerate*0.90
	//gen `Coin'_magicnumber = `Coin'_marketprice / `Coin'_exchangerate
	quietly count if `Coin'_profitbtc > 0
	disp "`Coin' % profitable: ", %3.1f 100 * r(N) / `total_obs'
	gen abs_profit = abs(`Coin'_profitpct)
	quietly summarize abs_profit
	drop abs_profit
	
}
/*
foreach x of local Coins {
	quietly sum `x'_profitpct, d
	disp %-4s "Coin", %7s "SD", %7s "mean", %8s "kurtosis"
	disp %-4s "`x'", %7.2f r(sd), %7.2f r(mean), %8.2f r(kurtosis) - 3
}
*/