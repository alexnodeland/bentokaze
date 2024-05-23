\* The_BentoKaze_Problem *\
Minimize
TotalCost: 1.2 'Apple' + 4.49 'Beef_Liver' + 3.99 'Blueberries'
 + 4.5 'Chia_Seeds' + 5.99 'Chicken_Breast' + 2.99 'Cottage_Cheese'
 + 3 'Flaxseed' + 7.99 'Salmon' + 6.49 'Turkey_Thigh' + 1.99 'Yogurt'
Subject To
TotalCarb: 25 'Apple' + 21 'Blueberries' + 12 'Chia_Seeds'
 + 3.4 'Cottage_Cheese' + 8 'Flaxseed' + 4.7 'Yogurt' <= 100
TotalFat: 0.3 'Apple' + 4.1 'Beef_Liver' + 0.3 'Blueberries'
 + 4.5 'Chia_Seeds' + 3.6 'Chicken_Breast' + 4.3 'Cottage_Cheese'
 + 3 'Flaxseed' + 13 'Salmon' + 8.5 'Turkey_Thigh' + 3.5 'Yogurt' >= 20
TotalProtein: 0.5 'Apple' + 25 'Beef_Liver' + 'Blueberries' + 2 'Chia_Seeds'
 + 31 'Chicken_Breast' + 11 'Cottage_Cheese' + 2 'Flaxseed' + 20 'Salmon'
 + 28 'Turkey_Thigh' + 5 'Yogurt' >= 50
TotalSalt: 0.2 'Beef_Liver' + 0.01 'Chia_Seeds' + 0.1 'Chicken_Breast'
 + 0.5 'Cottage_Cheese' + 0.03 'Flaxseed' + 0.1 'Salmon' + 0.2 'Turkey_Thigh'
 + 0.1 'Yogurt' <= 5
category_'Dairy': 'Cottage_Cheese' + 'Yogurt' >= 0.5
category_'Fruit': 'Apple' + 'Blueberries' >= 0.5
category_'Meat': 'Beef_Liver' + 'Chicken_Breast' + 'Salmon' + 'Turkey_Thigh'
 >= 0.5
category_'Seed': 'Chia_Seeds' + 'Flaxseed' >= 0.5
max_volume: 0.6 'Apple' + 1.04 'Beef_Liver' + 0.6 'Blueberries'
 + 0.65 'Chia_Seeds' + 1.04 'Chicken_Breast' + 1.03 'Cottage_Cheese'
 + 0.65 'Flaxseed' + 1.04 'Salmon' + 1.04 'Turkey_Thigh' + 1.03 'Yogurt'
 <= 100
End
