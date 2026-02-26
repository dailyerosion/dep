for yr in {2007..2025}; do
  for crop in corn soybeans; do
    # for datum in NE IA MN IA_NW IA_NC IA_NE IA_WC IA_C IA_EC IA_SW IA_SC IA_SE; do
    for datum in NE_NE NE_EC NE_SE MN_SW MN_WC MN_NW MN_C MN_SC MN_SE; do
      python nass_comparison.py --crop=$crop --year=$yr --plotv4 --plotv51 --datum=$datum
    done
  done
done
