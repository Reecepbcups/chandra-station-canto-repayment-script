ctrl + f `canto1qktq9k253tdq9xzkmtm5mxnxg3wkkgwjtedj8d` & change it to where ever you are repaying from (your cantod keys show KEYNAME -a)

```
cantod tx sign repayment_tx.json --from mykey --chain-id canto_7700-1 # save this signature to the repayment_tx.json signature line

copy paste the signatures array -> the repayment_tx.json at the bottom.

cantod tx broadcast repayment_tx.json --chain-id canto_7700-1 --gas 3000000 --from mykey
```