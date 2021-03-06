"""Web request and returns a Web response for products"""

from django.shortcuts import render, redirect, reverse, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.db.models.functions import Lower

from django.contrib.auth.decorators import login_required

from .models import Product, Category, Review
from .forms import ProductForm, RateForm


def all_products(request):
    """ A view to show all cakes, including sorting """

    products = Product.objects.all()
    query = None
    categories = None
    sort = None
    direction = None

    if request.GET:
        if 'sort' in request.GET:
            sortkey = request.GET['sort']
            sort = sortkey
            if sortkey == 'name':
                sortkey = 'lower_name'
                products = products.annotate(lower_name=Lower('name'))

            if 'direction' in request.GET:
                direction = request.GET['direction']
                if direction == 'desc':
                    sortkey = f'-{sortkey}'
            products = products.order_by(sortkey)

        if 'category' in request.GET:
            categories = request.GET['category'].split(',')
            products = products.filter(category__name__in=categories)
            categories = Category.objects.filter(name__in=categories)

        if 'q' in request.GET:
            query = request.GET['q']
            if not query:
                messages.error(request, "You didn't enter\
                any search criteria!")
                return redirect(reverse('products'))

            queries = Q(name__icontains=query) | \
                Q(description__icontains=query)
            products = products.filter(queries)

    current_sorting = f'{sort}_{direction}'

    context = {
        'products': products,
        'search_term': query,
        'current_categories': categories,
        'current_sorting': current_sorting,
    }

    return render(request, 'products/products.html', context)


def product_detail(request, product_id):
    """
    A view to show individual cake details
    including the reviews
    """
    product = get_object_or_404(Product, pk=product_id)
    reviews = Review.objects.all()

    context = {
        'product': product,
        'reviews': reviews,
    }

    return render(request, 'products/cake_detail.html', context)


@login_required
def add_product(request):
    """ Add a cake to the  store """
    if not request.user.is_superuser:
        messages.error(request, 'Sorry,\
        you do not have permission to do that!.')
        return redirect(reverse('home'))

    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save()
            messages.success(request, 'Successfully added cake!')
            return redirect(reverse('product_detail', args=[product.id]))
        else:
            messages.error(request, 'Failed to add cake.\
            Please ensure the "oven is on" and the form is valid.')
    else:
        form = ProductForm()

    template = 'products/add_product.html'
    context = {
        'form': form,
    }

    return render(request, template, context)


@login_required
def edit_product(request, product_id):
    """ Edit a cake in the website """
    if not request.user.is_superuser:
        messages.error(request, 'Sorry,\
        you do not have permission to do that!.')
        return redirect(reverse('home'))

    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Successfully updated the cake!')
            return redirect(reverse('product_detail', args=[product.id]))
        else:
            messages.error(request, 'Failed to update cake. Please ensure the \
                                     "oven is on" and the form is valid.')
    else:
        form = ProductForm(instance=product)
        messages.info(request, f'You are editing {product.name}')

    template = 'products/edit_product.html'
    context = {
        'form': form,
        'product': product,
    }

    return render(request, template, context)


@login_required
def delete_product(request, product_id):
    """ Delete a cake in the website """
    if not request.user.is_superuser:
        messages.error(request, 'Sorry,\
        you do not have permission to do that!.')
        return redirect(reverse('home'))

    product = get_object_or_404(Product, pk=product_id)
    product.delete()
    messages.success(request, 'Cake deleted!')

    return redirect(reverse('products'))


@login_required
def rate_product(request, product_id):
    """ Rate and review a product """
    product = get_object_or_404(Product, pk=product_id)
    user = request.user

    context = {
        'product': product,
    }

    if request.method == 'POST':
        form = RateForm(request.POST)
        if form.is_valid():
            rate = form.save(commit=False)
            rate.user = user
            rate.product = product
            rate.save()
            messages.success(request, 'Cake reviewed!')
            return redirect(reverse('product_detail', args=[product.id]))
    else:
        form = RateForm

    template = 'products/rate.html'

    context = {
        'form': form,
        'product': product,
    }

    return render(request, template, context)
