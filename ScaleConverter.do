include Header.do

foreach Coin of local Coins {
	if "``Coin'_scale'" == "H" local `Coin'_scale = 10^0
	if "``Coin'_scale'" == "K" local `Coin'_scale = 10^3
	if "``Coin'_scale'" == "M" local `Coin'_scale = 10^6
	if "``Coin'_scale'" == "G" local `Coin'_scale = 10^9
	if "``Coin'_scale'" == "T" local `Coin'_scale = 10^12
	if "``Coin'_scale'" == "P" local `Coin'_scale = 10^15
}