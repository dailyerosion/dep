for yr in {2022..2025}; do
  for crop in corn soybeans; do
    for datum in NE IA MN IA_NW IA_NC IA_NE IA_WC IA_C IA_EC IA_SW IA_SC IA_SE; do
      python nass_comparison.py --crop=$crop --year=$yr --plotv4 --datum=$datum
    done
  done
done
